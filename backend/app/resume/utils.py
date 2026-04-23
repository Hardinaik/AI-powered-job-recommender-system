import re
import groq
from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.exceptions import LLMError, EmbeddingError, PDFExtractionError
from langchain_core.exceptions import OutputParserException
from app.modelregistry import get_llm, safe_encode
from pydantic import ValidationError
from .schemas import ResumeExtraction
 
MAX_FILE_SIZE = 5 * 1024 * 1024
 
# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
 
def validate_pdf_extension(file: UploadFile) -> None:
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: '{file.filename}'. Only PDF files are supported.",
        )
 
 
def validate_file_size(file: UploadFile) -> None:
    if file.size and file.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({file.size / (1024*1024):.2f} MB). Max is 5 MB.",
        )
 
 
# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------
 
template = """
   ### ROLE
    You are a specialized HR Data Extraction Assistant. Your goal is to convert resume text into a strictly anonymized, machine-readable JSON format optimized for semantic search and vector embeddings.
 
    ### EXTRACTION RULES
 
    1. Skills (Semantic Summary):
    - Write a concise natural language summary of technical skills.
    - Group related skills together (e.g., programming languages, frameworks, databases).
    - Normalize variations (e.g., "Python3" → "Python", "Postgres" → "PostgreSQL").
    - Avoid keyword dumping. Write it as a meaningful sentence.
    - Keep it 1–2 sentences max.
 
    2. Work Experience Summary (1 line per role):
    - Cover ONLY actual employment (internships and full-time roles).
    - Each entry should be ONE concise sentence.
    - STRICT ANONYMIZATION: No company names, person names, or universities.
    - Format: [Role/Seniority] + [Tech Stack] + [Impact/Work Done]
    - If none, return empty list []
 
    3. Projects Summary (1 line per project):
    - Cover ONLY personal, academic, or open-source projects.
    - Each project must be ONE concise sentence.
    - STRICT ANONYMIZATION.
    - Focus on what was built + tech stack used.
    - If none, return empty list []
 
    ### INPUT DATA
    {resume}
 
    ### OUTPUT SPECIFICATION
    - Return ONLY valid JSON. No explanation, no markdown.
 
    {{
        "skills": "semantic skill summary",
        "work_experience": [
            "Role: summary"
        ],
        "projects": [
            "Project 1: summary",
            "Project 2: summary"
        ]
    }}
 
    ### EXAMPLE OUTPUT
 
    {{
        "skills": "Experience with programming languages such as Java and Python, frontend development using React, and backend systems built with FastAPI and PostgreSQL, along with knowledge of machine learning and generative AI concepts",
        "work_experience": [
            "Intern: Built time-series forecasting models using Python and implemented data preprocessing pipelines to improve prediction accuracy",
            "Software Engineer: Developed backend APIs and optimized database queries using Java and PostgreSQL to improve system performance"
        ],
        "projects": [
            "Project 1: Built an AI-powered job recommendation system using semantic search, embeddings, and FastAPI",
            "Project 2: Developed a machine learning pipeline for house price prediction with preprocessing, model evaluation, and regression models",
            "Project 3: Created a full-stack web application using React and Node.js with REST API integration"
        ]
    }}
"""
 
 
# ---------------------------------------------------------------------------
# Text extraction & cleaning
# ---------------------------------------------------------------------------

def extract_text_from_pdf(file_path: str) -> str:
    try:
        loader = PyMuPDFLoader(file_path)
        pages = loader.load()
        if not pages:
            raise PDFExtractionError("PDF appears to be empty or unreadable.")
        return "\n".join([page.page_content for page in pages])
    except PDFExtractionError:
        raise
    except Exception as e:
        raise PDFExtractionError(f"Failed to read PDF: {str(e)}")

 
def clean_resume_text(text: str) -> str:
    text = re.sub(r"\S+@\S+\.\S+", "", text)
    text = re.sub(r"\+?[\d][\d\s\-\.\(\)]{7,14}\d", "", text)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"(?:linkedin|github)\.com/\S+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()
 
 
# ---------------------------------------------------------------------------
# LLM extraction
# ---------------------------------------------------------------------------


def extract_json(filepath: str) -> ResumeExtraction:
    try:
        raw_text = extract_text_from_pdf(filepath)
    except PDFExtractionError:
        raise

    cleaned_text = clean_resume_text(raw_text)

    if not cleaned_text.strip():
        raise PDFExtractionError("Resume appears to be blank after cleaning.")

    try:
        prompt = PromptTemplate.from_template(template)
        chain = prompt | get_llm() | JsonOutputParser()
        raw: dict = chain.invoke({"resume": cleaned_text})

    except groq.RateLimitError:
        raise LLMError(
            "AI service is busy. Please try uploading again in a moment.",
            status_code=429,
        )
    except groq.AuthenticationError:
        raise LLMError("AI service authentication failed.", status_code=500)
    except groq.APITimeoutError:
        raise LLMError("AI service timed out. Please try again.", status_code=504)
    except groq.APIStatusError as e:
        raise LLMError(f"AI service error: {e.message}", status_code=502)
    except OutputParserException:
        raise LLMError(
            "AI returned an unexpected format. Please try again.",
            status_code=422,
        )
    except Exception as e:
        raise LLMError(f"Unexpected LLM error: {str(e)}", status_code=503)

    try:
        return ResumeExtraction.model_validate(raw)
    except ValidationError as e:
        raise LLMError(
            f"AI output missing required fields: {e.errors()[0]['msg']}",
            status_code=422,
        )

 
# ---------------------------------------------------------------------------
# Embedding creation
# ---------------------------------------------------------------------------
 
def create_resume_embedding(
    filepath: str,
) -> tuple[list[float], list[float] | None, list[float] | None]:
    """
    Processes a resume PDF and returns up to THREE normalized embeddings.
 
    Returns:
        skill_embedding   : always present (skills are required)
        work_embedding    : None if no work experience entries found
        project_embedding : None if no project entries found
 
    Storage mapping (Resume model columns):
        Resume.skill_embedding    ← skill_embedding   (never None)
        Resume.work_embedding     ← work_embedding    (nullable)
        Resume.project_embedding  ← project_embedding (nullable)
 
    Caller unpacks as:
        skill_emb, work_emb, project_emb = create_resume_embedding(path)
 
    During hybrid search / scoring:
        - If work_emb is None, skip the work-experience cosine term.
        - If project_emb is None, skip the project cosine term.
        - Reweight remaining terms so they still sum to 1.0.
    """


    document = extract_json(filepath)  # LLMError / PDFExtractionError propagate up

    resume_skills = document.skills.strip()
    work_items    = document.work_experience
    project_items = document.projects

    work_text    = " ".join(work_items).strip()    if work_items    else None
    project_text = " ".join(project_items).strip() if project_items else None

    resume_text = " ".join(
        [resume_skills]
        + (work_items    if work_items    else [])
        + (project_items if project_items else [])
    ).strip()

    # EmbeddingError propagates up — caller handles it
    skill_embedding   = safe_encode(resume_skills)
    work_embedding    = safe_encode(work_text)    if work_text    else None
    project_embedding = safe_encode(project_text) if project_text else None

    return resume_text, skill_embedding, work_embedding, project_embedding