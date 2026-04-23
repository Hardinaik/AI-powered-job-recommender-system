import os
import shutil
from uuid import UUID
from typing import List, Optional
import tempfile
import numpy as np
from rank_bm25 import BM25Okapi
from fastapi import APIRouter, Depends, Query, UploadFile, File, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Job, Location, Resume, JobSeekerProfile, JobSeekerPreferredLocation
from .schemas import RecJobResponse
from app.resume.utils import (
    validate_pdf_extension,
    validate_file_size,
    create_resume_embedding,
)
from app.utils import get_current_jobseeker
from app.exceptions import LLMError, EmbeddingError, PDFExtractionError


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Constants
BM25_K1: float = 1.5
BM25_B:  float = 0.75
RRF_K:   int   = 10


# Section 1 — BM25

def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text)
    return [t for t in text.split() if len(t) > 1]


def _rank_by_bm25(
    query_text: str,
    jobs:       list[Job],
) -> list[UUID]:
    tokenized_corpus = [_tokenize(job.job_description or "") for job in jobs]
    query_tokens     = _tokenize(query_text)

    bm25   = BM25Okapi(tokenized_corpus, k1=BM25_K1, b=BM25_B)
    scores = bm25.get_scores(query_tokens).tolist()

    scored = sorted(
        zip([job.job_id for job in jobs], scores),
        key=lambda x: x[1],
        reverse=True,
    )
    return [jid for jid, _ in scored]


# Section 2 — Semantic scoring

def _normalize(vec: list[float]) -> np.ndarray:
    """L2-normalize a vector. Returns zero vector if norm is zero."""
    arr  = np.array(vec, dtype=float)
    norm = np.linalg.norm(arr)
    return arr / norm if norm > 0 else arr


def _rank_by_semantic(
    jobs:        list[Job],
    skills_vec:  list[float],
    work_vec:    list[float] | None,
    project_vec: list[float] | None,
) -> list[UUID]:
    """
    Weighted cosine similarity between resume vectors and job embeddings.
    All vectors are L2-normalised once before dot product.

    Dynamic weights (always sum to 1.0):
        skills + work + project → 0.50 / 0.30 / 0.20
        skills + work only      → 0.60 / 0.40
        skills + project only   → 0.65 / 0.35
        skills only             → 1.00
    """
    has_work = work_vec    is not None
    has_proj = project_vec is not None

    if   has_work and has_proj:     w_skill, w_work, w_proj = 0.50, 0.30, 0.20
    elif has_work and not has_proj: w_skill, w_work, w_proj = 0.60, 0.40, 0.00
    elif not has_work and has_proj: w_skill, w_work, w_proj = 0.65, 0.00, 0.35
    else:                           w_skill, w_work, w_proj = 1.00, 0.00, 0.00

    # Normalize resume vectors once — reused across all jobs
    norm_skills = _normalize(skills_vec)
    norm_work = _normalize(work_vec)    if work_vec is not None else None
    norm_proj = _normalize(project_vec) if project_vec is not None else None

    scored = []
    for job in jobs:
        norm_skill_emb = job.skill_embedding 
        norm_job_emb   = job.job_embedding   

        score = (
            w_skill * (float(np.dot(norm_skills, norm_skill_emb)) if norm_skill_emb is not None else 0.0)
            + w_work  * (float(np.dot(norm_work,  norm_job_emb))  if norm_work  is not None and norm_job_emb is not None else 0.0)
            + w_proj  * (float(np.dot(norm_proj,  norm_job_emb))  if norm_proj  is not None and norm_job_emb is not None else 0.0)
        )
        scored.append((job.job_id, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [jid for jid, _ in scored]


# Section 3 — Reciprocal Rank Fusion

def _reciprocal_rank_fusion(
    semantic_ranking: list[UUID],
    bm25_ranking:     list[UUID],
    semantic_weight:  float = 0.60,
    bm25_weight:      float = 0.40,
) -> list[tuple[UUID, float]]:
    """
    Fuse two ranked lists via weighted RRF, rescaled to [0, 100].
    """
    all_ids   = list(dict.fromkeys(semantic_ranking + bm25_ranking))
    sem_rank  = {jid: i + 1 for i, jid in enumerate(semantic_ranking)}
    bm25_rank = {jid: i + 1 for i, jid in enumerate(bm25_ranking)}
    N_sem     = len(semantic_ranking) + 1
    N_bm25    = len(bm25_ranking)     + 1

    fused: list[tuple[UUID, float]] = [
        (
            jid,
            semantic_weight * (1.0 / (RRF_K + sem_rank.get(jid,  N_sem)))
            + bm25_weight   * (1.0 / (RRF_K + bm25_rank.get(jid, N_bm25))),
        )
        for jid in all_ids
    ]
    fused.sort(key=lambda x: x[1], reverse=True)

    if fused:
        top_score = fused[0][1] or 1.0
        fused = [(jid, round((s / top_score) * 100, 2)) for jid, s in fused]

    return fused


# Section 4 — Resume vectors

class ResumeVectors:
    """Bundles the three resume vectors and the BM25 query text."""

    def __init__(
        self,
        skills_vec:      list[float],
        work_vec:        list[float] | None,
        project_vec:     list[float] | None,
        bm25_query_text: str = "",
    ):
        self.skills_vec      = skills_vec
        self.work_vec        = work_vec
        self.project_vec     = project_vec
        self.bm25_query_text = bm25_query_text


def _resolve_profile_vectors(target_user_id: UUID, db: Session) -> ResumeVectors | None:
    saved_resume = (
        db.query(Resume)
        .filter(Resume.user_id == target_user_id)
        .first()
    )
    if not saved_resume:
        return None

    return ResumeVectors(
        skills_vec      = list(saved_resume.skill_embedding),
        work_vec        = list(saved_resume.work_embedding)    if saved_resume.work_embedding    is not None else None,
        project_vec     = list(saved_resume.project_embedding) if saved_resume.project_embedding is not None else None,
        bm25_query_text = saved_resume.resume_text or "",
    )



def _resolve_uploaded_vectors(resume_file: UploadFile, target_user_id: UUID) -> ResumeVectors:
    validate_pdf_extension(resume_file)
    validate_file_size(resume_file)

    tmp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
    try:
        with os.fdopen(tmp_fd, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)
        bm25_text, skill_emb, work_emb, project_emb = create_resume_embedding(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return ResumeVectors(
        skills_vec      = skill_emb,
        work_vec        = work_emb,
        project_vec     = project_emb,
        bm25_query_text = bm25_text,
    )

# Section 5 — Filters

class JobFilters:
    """Hard-filter parameters resolved from either the profile or manual input."""

    def __init__(
        self,
        domain_id:    int | None,
        experience:   int | None,
        location_ids: list[int] | None,
    ):
        self.domain_id    = domain_id
        self.experience   = experience
        self.location_ids = location_ids


def _resolve_profile_filters(target_user_id: UUID, db: Session) -> JobFilters:
    profile = (
        db.query(JobSeekerProfile)
        .filter(JobSeekerProfile.user_id == target_user_id)
        .first()
    )
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="No jobseeker profile found. Please complete your profile first.",
        )

    pref_locs    = db.query(JobSeekerPreferredLocation).filter(JobSeekerPreferredLocation.user_id == target_user_id).all()
    location_ids = [pl.location_id for pl in pref_locs] if pref_locs else None

    return JobFilters(
        domain_id    = profile.preferred_domain_id,
        experience   = profile.experience,
        location_ids = location_ids,
    )


# Section 6 — Hard filter query

def _apply_hard_filters(db: Session, filters: JobFilters) -> list[Job]:
    
    # Step 1: Build a subquery to get matching job_ids only
    id_query = select(Job.job_id)

    if filters.domain_id is not None:
        id_query = id_query.where(Job.industry_domain_id == filters.domain_id)

    if filters.experience is not None:
        id_query = id_query.where(Job.min_experience <= filters.experience)

    if filters.location_ids:
        id_query = (
            id_query
            .join(Job.locations)
            .where(Location.id.in_(filters.location_ids))
            .distinct()  # one job_id even if multiple locations matched
        )

    matched_ids = id_query.scalar_subquery()

    # Step 2: Load full Job objects cleanly with locations eager loaded
    jobs = (
        db.query(Job)
        .options(joinedload(Job.locations))
        .filter(Job.job_id.in_(matched_ids))
        .all()
    )

    return jobs

# Section 7 — Response builders

def _build_hybrid_response(
    jobs:    list[Job],
    vectors: ResumeVectors,
    limit:   int,
) -> list[RecJobResponse]:
    """
    1. Semantic ranking  — weighted cosine similarity (normalized vectors)
    2. BM25 ranking      — keyword match on job descriptions
    3. RRF fusion        — combine both rankings
    4. Return top `limit` jobs
    """
    semantic_ranking = _rank_by_semantic(
        jobs,
        vectors.skills_vec,
        vectors.work_vec,
        vectors.project_vec,
    )

    bm25_ranking = (
        _rank_by_bm25(vectors.bm25_query_text, jobs)
        if vectors.bm25_query_text.strip()
        else semantic_ranking
    )

    fused_scores = _reciprocal_rank_fusion(
        semantic_ranking = semantic_ranking,
        bm25_ranking     = bm25_ranking,
        semantic_weight  = 0.60,
        bm25_weight      = 0.40,
    )

    job_map: dict[UUID, Job] = {job.job_id: job for job in jobs}

    return [
        RecJobResponse(
            job_id          = jid,
            job_title       = job_map[jid].job_title,
            locations       = [loc.name for loc in job_map[jid].locations],
            job_description = job_map[jid].job_description,
            min_experience  = job_map[jid].min_experience,
            company_name    = job_map[jid].company_name,
            match_score     = score,
        )
        for jid, score in fused_scores[:limit]
        if jid in job_map
    ]


def _build_fallback_response(jobs: list[Job], limit: int) -> list[RecJobResponse]:
    """Newest-first when no resume vectors available."""
    return [
        RecJobResponse(
            job_id          = job.job_id,
            job_title       = job.job_title,
            locations       = [loc.name for loc in job.locations],
            job_description = job.job_description,
            min_experience  = job.min_experience,
            company_name    = job.company_name,
            match_score     = 0.0,
        )
        for job in jobs[:limit]
    ]


# Section 8 — Endpoint

@router.post("/jobs", response_model=List[RecJobResponse])
async def get_recommended_jobs(
    use_profile:  bool                 = Query(False),
    domain_id:    Optional[int]        = Query(None),
    location_ids: Optional[List[int]]  = Query(None),
    experience:   Optional[int]        = Query(None),
    limit:        int                  = Query(default=10, ge=1, le=100),
    resume_file:  Optional[UploadFile] = File(None),
    db:           Session              = Depends(get_db),
    current_user: dict                 = Depends(get_current_jobseeker),
):
    target_user_id = UUID(current_user["user_id"])

    # 1. Resolve hard filters --------------------------------------------------
    filters = (
        _resolve_profile_filters(target_user_id, db)
        if use_profile
        else JobFilters(
            domain_id    = domain_id,
            experience   = experience,
            location_ids = location_ids,
        )
    )

    # 2. Fetch all jobs passing hard filters -----------------------------------
    filtered_jobs = _apply_hard_filters(db, filters)
    if not filtered_jobs:
        return []

    # 3. Resolve resume vectors ------------------------------------------------
    vectors: ResumeVectors | None = None
    if use_profile:
        vectors = _resolve_profile_vectors(target_user_id, db)
    elif resume_file:
        try:
            vectors = _resolve_uploaded_vectors(resume_file, target_user_id)
        except (LLMError, PDFExtractionError, EmbeddingError) as e:
            status = e.status_code if hasattr(e, "status_code") else 422
            raise HTTPException(status_code=status, detail=str(e))

    # 4. Rank and return -------------------------------------------------------
    if vectors is not None:
        return _build_hybrid_response(filtered_jobs, vectors, limit)

    # Fallback — no resume, return newest jobs
    filtered_jobs.sort(key=lambda j: j.posted_at, reverse=True)
    return _build_fallback_response(filtered_jobs, limit)