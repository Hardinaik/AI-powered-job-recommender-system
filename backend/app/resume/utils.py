import re
import os
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from sentence_transformers import SentenceTransformer

load_dotenv()

MAX_FILE_SIZE = 5 * 1024 * 1024

# ---------------------------------------------------------------------------
# Lazy singletons — initialized on first use, not at import time.
# This prevents crashes when API_KEY is missing or during testing.
# ---------------------------------------------------------------------------
_embedding_model = None
_llm = None


def get_llm() -> ChatGoogleGenerativeAI:
    global _llm
    if _llm is None:
        api_key = os.getenv("API_KEY")
        if not api_key:
            raise RuntimeError("API_KEY environment variable is not set.")
        _llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=api_key,
        )
    return _llm


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")
    return _embedding_model


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
    """
    Reads the entire file into memory to get an accurate size,
    then resets the pointer so downstream code can read it normally.
    Using seek/tell on SpooledTemporaryFile (FastAPI's UploadFile backing)
    is unreliable — reading is the safe approach.
    """
    contents = file.file.read()
    file.file.seek(0)
    size = len(contents)
    if size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size / (1024 * 1024):.2f} MB). Maximum allowed size is 5 MB.",
        )


# ---------------------------------------------------------------------------
# Resume text extraction & cleaning
# ---------------------------------------------------------------------------

template = """
    ### ROLE
    You are a specialized HR Data Extraction Assistant. Your goal is to convert resume text into a strictly anonymized, machine-readable JSON format for unbiased screening and vector embedding.
    
    ### EXTRACTION RULES
    
    1. **Skills (Normalized List)**:
    - Extract a clean list of technical and soft skills.
    - Normalize variations (e.g., "Python3" → "Python", "Postgres" → "PostgreSQL").
    - Return as a SPACE-SEPARATED string (no commas). Example: "Python FastAPI PostgreSQL React Docker".
    
    2. **Education (Highest Degree)**:
    - Extract the highest degree only (e.g., "B.Tech in Computer Science").
    - Do NOT include university names.
    
    3. **Work Experience Summary (2-3 sentences)**:
    - Cover ONLY actual employment history (internships and full-time jobs count).
    - If no employment history exists, return an empty string "".
    - STRICT ANONYMIZATION: No names, company names, or university names.
    - Formula: [Seniority/Role] + [Core Tech Stack] + [Impact/Action].
    
    4. **Projects Summary (1-2 sentences)**:
    - Cover ONLY personal, academic, or open-source projects (not actual jobs).
    - If no projects exist, return an empty string "".
    - STRICT ANONYMIZATION: No names, company names, or university names.
    - Focus on tech stack used and what was built/achieved.
    
    ### INPUT DATA
    {resume}
    
    ### OUTPUT SPECIFICATION
    - Return ONLY the JSON object. No preamble, no markdown code blocks.
    - Follow this exact schema:
    
    {{
        "skills": "skill1 skill2 skill3",
        "education": "Degree Name (e.g. B.Tech in Computer Science)",
        "work_experience_summary": "2-3 sentences on actual employment only. Empty string if none.",
        "projects_summary": "1-2 sentences on personal/academic projects only. Empty string if none."
    }}
"""



def extract_text_from_pdf(file_path: str) -> str:
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return "\n".join([page.page_content for page in pages])


def clean_resume_text(text: str) -> str:
    """
    Strips PII from raw resume text before sending to the LLM.

    Removes:
      - Email addresses
      - Phone numbers (all formats including E.164 e.g. +919876543210)
      - URLs (http/https and bare www.)
      - LinkedIn and GitHub profile URLs (common PII in resumes)

    Then collapses excess whitespace left behind by the removals.
    """
    # Emails
    text = re.sub(r"\S+@\S+\.\S+", "", text)

    # Phone numbers — aggressive pattern covers:
    #   E.164 compact  : +919876543210
    #   E.164 spaced   : +91 98765 43210
    #   US formatted   : (415) 555-1234
    #   Dashes/dots    : 415-555-1234 / 415.555.1234
    #   Plain 10-digit : 9876543210
    text = re.sub(r"\+?[\d][\d\s\-\.\(\)]{7,14}\d", "", text)

    # URLs
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # LinkedIn / GitHub profile handles
    text = re.sub(r"(?:linkedin|github)\.com/\S+", "", text, flags=re.IGNORECASE)

    # Collapse whitespace artifacts left by removals
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# LLM extraction & embedding
# ---------------------------------------------------------------------------

def extract_json(filepath: str) -> dict:
    """
    Extracts structured resume data from a PDF using the LLM chain.
 
    Returns a dict with keys:
        - skills                 (space-separated string)
        - education
        - work_experience_summary
        - projects_summary
 
    FIX 4: Added validation — if Gemini omits required keys or returns
    empty values for both summaries, we raise a clear 422 error instead
    of silently encoding empty strings into vectors (which match everything
    badly and pollute the recommendation scores).
    """
    raw_text = extract_text_from_pdf(filepath)
    cleaned_text = clean_resume_text(raw_text)
 
    prompt = PromptTemplate.from_template(template)
    chain = prompt | get_llm() | JsonOutputParser()
 
    extracted: dict = chain.invoke({"resume": cleaned_text})
 
    # Validate required keys are present
    required_keys = {"skills", "education", "work_experience_summary", "projects_summary"}
    missing_keys = required_keys - set(extracted.keys())
    if missing_keys:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Resume parsing failed — LLM response missing fields: {missing_keys}. "
                "Try a cleaner or more complete PDF."
            ),
        )
 
    # Validate that at least one content field is non-empty
    # (a resume with no skills AND no summaries is unembeddable)
    if not extracted.get("skills", "").strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "Resume parsing failed — could not extract any skills. "
                "Ensure the PDF contains readable text (not a scanned image)."
            ),
        )
 
    if not extracted.get("work_experience_summary", "").strip() and \
       not extracted.get("projects_summary", "").strip():
        raise HTTPException(
            status_code=422,
            detail=(
                "Resume parsing failed — could not extract work experience or projects. "
                "Ensure the PDF contains readable text (not a scanned image)."
            ),
        )
 
    return extracted
 
 
def create_resume_embedding(filepath: str) -> tuple[list[float], list[float], list[float]]:
    """
    Processes a resume PDF and returns THREE normalized embeddings.
 
    Returns:
        skill_embedding   : embedding of the extracted skills string
        work_embedding    : embedding of the work experience summary
        project_embedding : embedding of the projects summary
 
    Storage mapping (matches Resume model columns):
        Resume.skill_embedding    ← skill_embedding   (index 0)
        Resume.resume_embedding   ← work_embedding    (index 1)
        Resume.project_embedding  ← project_embedding (index 2)  ← NEW COLUMN NEEDED
 
    Caller unpacks as:
        skill_emb, work_emb, project_emb = create_resume_embedding(path)
 
    NOTE: You need to add a `project_embedding` column to your Resume model:
        project_embedding = mapped_column(Vector(384), nullable=True)
 
    And update the route to store and use this third vector.
    """
    document = extract_json(filepath)
    model = get_embedding_model()
 
    # FIX 3 (applied here): skills are already space-separated from the prompt.
    # We still strip any accidental commas defensively.
    resume_skills: str = document.get("skills", "").replace(",", " ").strip()
    work_summary: str = document.get("work_experience_summary", "").strip()
    projects_summary: str = document.get("projects_summary", "").strip()
 
    # If one summary is empty, fall back to the other so we never encode
    # a blank string (blank → near-zero vector → random cosine matches).
    if not work_summary:
        work_summary = projects_summary
    if not projects_summary:
        projects_summary = work_summary
 
    skill_embedding: list[float] = model.encode(
        resume_skills,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).tolist()
 
    work_embedding: list[float] = model.encode(
        work_summary,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).tolist()
 
    project_embedding: list[float] = model.encode(
        projects_summary,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).tolist()
 
    return skill_embedding, work_embedding, project_embedding
