import re
from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.modelregistry import get_llm, get_embedding_model
 
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
    contents = file.file.read()
    file.file.seek(0)
    size = len(contents)
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size / (1024 * 1024):.2f} MB). Maximum allowed size is 5 MB.",
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
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return "\n".join([page.page_content for page in pages])
 
 
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
 
def extract_json(filepath: str) -> dict:
    """
    Extracts structured resume data from a PDF using the LLM chain.
 
    Returns a dict with keys:
        - skills           (non-empty string — REQUIRED)
        - work_experience  (list of strings — may be empty [])
        - projects         (list of strings — may be empty [])
    """
    raw_text = extract_text_from_pdf(filepath)
    cleaned_text = clean_resume_text(raw_text)
 
    prompt = PromptTemplate.from_template(template)
    chain = prompt | get_llm() | JsonOutputParser()
    extracted: dict = chain.invoke({"resume": cleaned_text})
 
    # Validate required keys are present
    required_keys = {"skills", "work_experience", "projects"}
    missing_keys = required_keys - set(extracted.keys())
    if missing_keys:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Resume parsing failed — LLM response missing fields: {missing_keys}. "
                "Try a cleaner or more complete PDF."
            ),
        )
 
    # skills is the only hard-required non-empty field
    if not extracted.get("skills", "").strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "Resume parsing failed — could not extract any skills. "
                "Ensure the PDF contains readable text (not a scanned image)."
            ),
        )
 
    # Ensure work_experience and projects are lists (guard against LLM returning strings)
    if not isinstance(extracted.get("work_experience"), list):
        extracted["work_experience"] = []
    if not isinstance(extracted.get("projects"), list):
        extracted["projects"] = []
 
    return extracted
 
 
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
    document = extract_json(filepath)
    model = get_embedding_model()
 
    resume_skills: str = document["skills"].strip()
 
    # Work experience — join list items into one paragraph; None if empty list
    work_items: list[str] = document.get("work_experience", [])
    work_text: str | None = " ".join(work_items).strip() if work_items else None
 
    # Projects — same treatment
    project_items: list[str] = document.get("projects", [])
    project_text: str | None = " ".join(project_items).strip() if project_items else None

    resume_text: str = " ".join(
        [resume_skills]
        + (work_items    if work_items    else [])
        + (project_items if project_items else [])
    ).strip()

    def _encode(text: str) -> list[float]:
        return model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        ).tolist()
 
    skill_embedding: list[float] = _encode(resume_skills)
    work_embedding: list[float] | None = _encode(work_text) if work_text else None
    project_embedding: list[float] | None = _encode(project_text) if project_text else None
 
    return resume_text,skill_embedding, work_embedding, project_embedding