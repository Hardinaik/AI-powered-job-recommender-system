import re
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from sentence_transformers import SentenceTransformer, util
import os
from dotenv import load_dotenv


template = """
Read the following Job Description:
{jd}

Extract the key details and return the output strictly in valid JSON format.

Instructions:

1. "job_role":
   - Extract the exact job title.

2. "skills":
   - Extract all technical and relevant skills.
   - Normalize variations:
       * "python programming", "python3" → "python"
       * "postgres", "postgres db" → "postgresql"
   - Remove duplicates.
   - Return as a single comma-separated string.
   - Example format: "python, java, c++, distributed systems"

3. "education":
   - Extract only the required education qualification.

4. "responsibilities":
   - Summarize core responsibilities in 3–5 sentences.
   - Focus only on technologies, type of work, and required competencies.
   - Exclude company name, perks, and application process.
   - Return as a single string.

Return strictly in this format:

{{
  "job_role": "",
  "skills": "",
  "education": "",
  "responsibilities": ""
}}
"""



def create_llm_model():
    load_dotenv()
    API_Key=os.getenv("API_Key")
    llm=ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key= API_Key
    )
    return llm

def extract_json(jd):
    llm = create_llm_model() 
    prompt = PromptTemplate.from_template(template)
    chain=prompt | llm | JsonOutputParser()
    extracted_jd = chain.invoke({"jd": jd})
    return extracted_jd


def create_job_embedding(jd):
    document = extract_json(jd)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    job_skills = document['skills']
    job_work_summary = document['responsibilities']

    embedding_skills = model.encode(
        job_skills, convert_to_numpy=True, normalize_embeddings=True
    ).tolist()  
    embedding_res = model.encode(
        job_work_summary, convert_to_numpy=True, normalize_embeddings=True
    ).tolist()

    return embedding_skills, embedding_res


