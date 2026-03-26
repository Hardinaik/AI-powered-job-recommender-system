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
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
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
   - Normalize variations (e.g., "Python3" to "Python", "Postgres" to "PostgreSQL").
   - Return as a single string of comma-separated values.

2. **Education (Highest Degree)**: 
   - Extract the highest Degree only (e.g., "B.Tech in Computer Science", "M.S. in Data Science").
   - Do NOT include university names.

3. **Anonymized Summary (3-5 Sentences)**: 
   - **STRICT ANONYMIZATION**: Remove all PII. Do NOT mention Names, Company Names, or University Names.
   - **CONTENT FOCUS**: Consolidate all work experience and projects into a dense 3-5 sentence narrative. 
   - Use the formula: **[Seniority/Role] + [Core Tech Stack] + [Impact/Action]**.
   - Ensure specific domains (e.g., Java Backend, Time-series, LLMs, Sales Forecasting) are mentioned.
   - Just focus on past work experience and projects — no other things.

### INPUT DATA
{resume}

### OUTPUT SPECIFICATION
- Return ONLY the JSON object. No preamble or markdown code blocks.
- Follow this exact schema:

{{
    "skills": "skill1, skill2, skill3",
    "education": "Degree Name (e.g. B.Tech in Computer Science)",
    "summary_of_experience": "A dense 3-5 sentence professional summary focused on technical impact and stack."
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
    Extracts structured resume data (skills, education, summary) from a PDF
    using the LLM chain. Returns a dict with keys:
        - skills
        - education
        - summary_of_experience
    """
    raw_text = extract_text_from_pdf(filepath)
    cleaned_text = clean_resume_text(raw_text)

    prompt = PromptTemplate.from_template(template)
    chain = prompt | get_llm() | JsonOutputParser()

    extracted: dict = chain.invoke({"resume": cleaned_text})
    return extracted


def create_resume_embedding(filepath: str) -> tuple[list[float], list[float]]:
    """
    Processes a resume PDF and returns two normalized embeddings:

    Returns:
        skill_embedding   : embedding of the extracted skills string
        work_embedding    : embedding of the extracted experience summary

    Storage mapping (matches Resume model columns):
        Resume.skill_embedding    ← skill_embedding  (index 0)
        Resume.resume_embedding   ← work_embedding   (index 1)
    """
    document = extract_json(filepath)

    resume_skills: str = document.get("skills", "")
    resume_work_summary: str = document.get("summary_of_experience", "")

    model = get_embedding_model()

    skill_embedding: list[float] = model.encode(
        resume_skills,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).tolist()

    work_embedding: list[float] = model.encode(
        resume_work_summary,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).tolist()

    # Return order: (skill_embedding, work_embedding)
    # Caller unpacks as: skill_emb, work_emb = create_resume_embedding(path)
    return skill_embedding, work_embedding