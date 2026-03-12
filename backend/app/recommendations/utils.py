import re
import os
from dotenv import load_dotenv
from fastapi import HTTPException, UploadFile
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from sentence_transformers import SentenceTransformer

# Load environment variables
load_dotenv()

# Initialize model globally to save RAM and improve speed
# Since you have 8GB RAM, loading this once is much safer
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
api_key = os.getenv("API_KEY")
llm= ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=api_key
    )
MAX_FILE_SIZE = 5 * 1024 * 1024  

def validate_pdf_extension(file: UploadFile):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid file type: {file.filename}. Only PDF is supported."
        )

def validate_file_size(file: UploadFile):
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"File too large ({file_size / (1024*1024):.2f}MB). Max limit is 5MB."
        )



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
   - Ensure specific domains (e.g., Java Backend,Time-series, LLMs, Sales Forecasting) are mentioned.
   - Just focus on past work experience and project no other things.

### INPUT DATA
{resume}

### OUTPUT SPECIFICATION
- Return ONLY the JSON object. No preamble or markdown code blocks.
- Follow this exact schema:

{{
    "skills": "skill1, skill2, skill3",
    "education": "Degree Name (B.Tech in computer science, B.sc in Maths)",
    "summary_of_experience": "A dense 3-5 sentence professional summary focused on technical impact and stack."
}}
"""
    

def extract_text_from_pdf(file_path):
    loader = PyMuPDFLoader(file_path)
    pages = loader.load()
    return "\n".join([page.page_content for page in pages])

def clean_resume_text(text):
    text = re.sub(r'\S+@\S+\.\S+', "", text)
    phone_pattern = r'(\+?\d{1,3}[\s-]?)?\d{10}'
    text = re.sub(phone_pattern, "", text)
    text = re.sub(r'https?://\S+|www\.\S+', "", text)
    return text.strip()

def extract_json(filepath):
    raw_text = extract_text_from_pdf(filepath)
    cleaned_text = clean_resume_text(raw_text)
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | llm | JsonOutputParser()
    
    # Corrected: Added return and structured the response
    extracted = chain.invoke({"resume": cleaned_text})
    return extracted, cleaned_text

def create_resume_embedding(filepath):
    # Pass the filepath and unpack the returned tuple
    document, resume_text = extract_json(filepath)
    
    # Use the globally loaded model
    resume_skills = document.get('skills', "")
    resume_work_summary = document.get('summary_of_experience', "")

    # Generate embeddings
    embedding_skills = embedding_model.encode(
        resume_skills, convert_to_numpy=True, normalize_embeddings=True
    ).tolist()  
    
    embedding_work_summary = embedding_model.encode(
        resume_work_summary, convert_to_numpy=True, normalize_embeddings=True
    ).tolist()

    return embedding_skills, embedding_work_summary, resume_text