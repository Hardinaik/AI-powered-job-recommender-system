import os
from dotenv import load_dotenv
from fastapi import HTTPException
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from sentence_transformers import SentenceTransformer

load_dotenv()

# ---------------------------------------------------------------------------
# Lazy singletons
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
# Prompt template
# ---------------------------------------------------------------------------

# WHY ONE JOB SUMMARY (not two):
#
# Resume side has two summaries:
#   resume.resume_embedding  = work experience  ("built X using Y at a company")
#   resume.project_embedding = projects         ("built X using Y as a side project")
#
# Both should compare against what the job DOES day-to-day — not against
# candidate credential requirements ("must have 5 years Java").
#
# "requirements_summary" was wrong as a separate embedding because:
#   JD requirement: "worked on Java"
#   Resume project:  no Java projects, but work experience has Java
#   → project_embedding vs requirements_embedding would miss this match entirely
#
# Correct alignment:
#   resume.skill_embedding   ↔  job.skill_embedding   (skills vs skills)
#   resume.resume_embedding  ↔  job.job_embedding     (work exp vs what job does)
#   resume.project_embedding ↔  job.job_embedding     (projects vs what job does)
#
# So job_embedding should be ONE rich summary that folds responsibilities
# AND domain expertise together as work context — not as credential checklists.

template = """
Read the following Job Description:
{jd}

Extract the key details and return the output strictly in valid JSON format.

Instructions:

1. "job_role":
   - Extract the exact job title.

2. "skills":
   - Extract all technical and relevant skills mentioned anywhere in the JD.
   - Normalize variations:
       * "python programming", "python3" → "python"
       * "postgres", "postgres db" → "postgresql"
   - Remove duplicates.
   - Return as a SPACE-SEPARATED string (no commas).
   - Example: "python java fastapi postgresql docker kubernetes"

3. "education":
   - Extract only the required education qualification.
   - Example: "B.Tech in Computer Science or equivalent"

4. "job_summary":
   - Write a dense 3-5 sentence paragraph that captures BOTH what the role does
     AND the domain/technical context the work demands.
   - Combine responsibilities and requirements into one coherent work description.
   - Formula: [What the engineer builds/maintains] + [Tech stack used] +
              [Team/system context] + [Domain expertise the work demands].
   - Good example:
     "Engineers in this role design and maintain distributed backend services
      using Java and Spring Boot, integrating with Kafka event streams and
      PostgreSQL databases. The work involves building low-latency APIs for
      a fintech platform, collaborating with frontend and data teams.
      Deep expertise in JVM performance tuning and microservices architecture
      is central to the day-to-day work."
   - Exclude: company name, perks, salary, application process.
   - Express experience requirements as work context, not credentials:
     WRONG: "Must have 5 years of Java experience."
     RIGHT: "The role demands deep expertise in Java for production-grade services."

Return strictly in this format (no markdown, no preamble):

{{
  "job_role": "",
  "skills": "",
  "education": "",
  "job_summary": ""
}}
"""


def extract_json(jd: str) -> dict:
    """
    Extracts structured job data from a raw job description string.

    Returns a dict with keys:
        - job_role
        - skills       (space-separated, no commas)
        - education
        - job_summary  (rich combined responsibilities + domain context)
    """
    prompt = PromptTemplate.from_template(template)
    chain = prompt | get_llm() | JsonOutputParser()
    extracted: dict = chain.invoke({"jd": jd})

    required_keys = {"job_role", "skills", "job_summary"}
    missing_keys = required_keys - set(extracted.keys())
    if missing_keys:
        raise HTTPException(
            status_code=422,
            detail=f"Job description parsing failed — LLM response missing fields: {missing_keys}.",
        )

    if not extracted.get("skills", "").strip():
        raise HTTPException(
            status_code=422,
            detail="Job description parsing failed — could not extract any skills.",
        )

    if not extracted.get("job_summary", "").strip():
        raise HTTPException(
            status_code=422,
            detail="Job description parsing failed — could not extract a job summary.",
        )

    return extracted


def create_job_embedding(jd: str) -> tuple[list[float], list[float]]:
    """
    Processes a raw job description and returns TWO normalized embeddings.

    Returns:
        skill_embedding  : embedding of the extracted skills string
        job_embedding    : embedding of the rich job summary

    Storage mapping (Job model — no new columns needed):
        Job.skill_embedding  ← skill_embedding   (index 0)
        Job.job_embedding    ← job_embedding      (index 1)

    Caller unpacks as:
        skill_emb, job_emb = create_job_embedding(jd)

    Cosine similarity alignment with resume side:
        Resume.skill_embedding   ↔  Job.skill_embedding   (skills vs skills)
        Resume.resume_embedding  ↔  Job.job_embedding     (work exp vs job context)
        Resume.project_embedding ↔  Job.job_embedding     (projects vs job context)

    Both resume.resume_embedding AND resume.project_embedding compare against
    the same job.job_embedding. This is correct — the job summary describes
    work being done, which is the right counterpart for both employment history
    and personal projects. The route weights them differently:
        0.50 × skill similarity
        0.30 × work_exp vs job_summary
        0.20 × projects vs job_summary
    """
    document = extract_json(jd)
    model = get_embedding_model()

    job_skills: str = document.get("skills", "").replace(",", " ").strip()
    job_summary: str = document.get("job_summary", "").strip()

    skill_embedding: list[float] = model.encode(
        job_skills,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).tolist()

    job_embedding: list[float] = model.encode(
        job_summary,
        convert_to_numpy=True,
        normalize_embeddings=True,
    ).tolist()

    return skill_embedding, job_embedding