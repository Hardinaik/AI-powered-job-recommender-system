
from fastapi import HTTPException
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.exceptions import OutputParserException
from app.modelregistry import get_llm,safe_encode
from app.exceptions import LLMError, EmbeddingError
from pydantic import ValidationError
from .schemas import JobExtraction
import groq

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

1. "skills":
   - Extract all technical and relevant skills mentioned anywhere in the JD.
   - Normalize variations:
       * "python programming", "python3" → "python"
       * "postgres", "postgres db" → "postgresql"
   - Remove duplicates.
   - Return as a SPACE-SEPARATED string (no commas).
   - Example: "python java fastapi postgresql docker kubernetes"


2. "job_summary":
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
  "job_summary": ""
}}
"""


def extract_json(jd: str) -> JobExtraction:
    prompt = PromptTemplate.from_template(template)

    try:
        chain = prompt | get_llm() | JsonOutputParser()
        raw: dict = chain.invoke({"jd": jd})

    except groq.RateLimitError:
        raise LLMError(
            "AI service is busy right now. Please try again in a moment.",
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
        return JobExtraction.model_validate(raw)
    except ValidationError as e:
        raise LLMError(
            f"AI output missing required fields: {e.errors()[0]['msg']}",
            status_code=422,
        )

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

    job_skills: str = document.skills.replace(",", " ").strip()
    job_summary: str = document.job_summary.strip()

    # EmbeddingError propagates up — caller handles it
    skill_embedding = safe_encode(job_skills)
    job_embedding   = safe_encode(job_summary)

    return skill_embedding, job_embedding

