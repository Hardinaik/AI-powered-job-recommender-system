import os
import shutil
from uuid import UUID
from typing import List, Optional

import numpy as np
from rank_bm25 import BM25Okapi
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
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

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

# Constants

# BM25 hyperparameters (passed directly to BM25Okapi)
# k1 = 1.5  — term-frequency saturation; 1.2–2.0 is standard.
#             1.5 suits technical JDs with moderate keyword repetition.
# b  = 0.75 — length normalisation; canonical default.
#             Prevents very short JDs from dominating purely by density.
BM25_K1: float = 1.5
BM25_B:  float = 0.75

RRF_K: int = 10

CANDIDATE_MULTIPLIER: int = 10


# Section 1 — BM25  (via rank_bm25)

def _tokenize(text: str) -> list[str]:
    """Lowercase, strip punctuation, split on whitespace."""
    text = text.lower()
    text = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text)
    return [t for t in text.split() if len(t) > 1]


def _rank_by_bm25(
    query_text: str,
    jobs: list[Job],
) -> list[UUID]:
    """
    Rank candidate jobs by BM25 score against `query_text` using BM25Okapi.
    Returns job_ids ordered best → worst.
    """
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

def _cosine_sim(a: list[float], b: list[float] | None) -> float:
    """
    Cosine similarity via dot product of two already-normalised unit vectors.
    For L2-normalised embeddings: cosine_similarity = dot_product.
    Returns 0.0 if b is None (missing embedding → no contribution).
    """
    if b is None:
        return 0.0
    return float(np.dot(np.array(a, dtype=float), np.array(b, dtype=float)))


def _rank_by_semantic(
    jobs:        list[Job],
    skills_vec:  list[float],
    work_vec:    list[float] | None,
    project_vec: list[float] | None,
) -> list[UUID]:
    """
    Rank candidate jobs by weighted cosine similarity.

    Weights adjust dynamically so they always sum to 1.0:
        skills + work + project available → 0.50 / 0.30 / 0.20
        skills + work only               → 0.60 / 0.40
        skills + project only            → 0.65 / 0.35
        skills only                      → 1.00

    Returns job_ids ordered best → worst (higher similarity = better).
    """
    has_work = work_vec    is not None
    has_proj = project_vec is not None

    if   has_work and has_proj:     w_skill, w_work, w_proj = 0.50, 0.30, 0.20
    elif has_work and not has_proj: w_skill, w_work, w_proj = 0.60, 0.40, 0.00
    elif not has_work and has_proj: w_skill, w_work, w_proj = 0.65, 0.00, 0.35
    else:                           w_skill, w_work, w_proj = 1.00, 0.00, 0.00

    scored: list[tuple[UUID, float]] = [
        (
            job.job_id,
            w_skill * _cosine_sim(skills_vec,  job.skill_embedding)
            + w_work  * _cosine_sim(work_vec,  job.job_embedding)
            + w_proj  * _cosine_sim(project_vec, job.job_embedding),
        )
        for job in jobs
    ]
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
    Fuse two ranked lists into one via weighted RRF, rescaled to [0, 100].

    Formula:
        score(d) = semantic_weight * 1/(RRF_K + rank_semantic(d))
                 + bm25_weight    * 1/(RRF_K + rank_bm25(d))

    Ranks are 1-indexed; documents absent from a list receive rank
    len(list)+1 so they are penalised but not discarded.
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

    # Rescale to [0, 100]
    if fused: 
        top_score = fused[0][1] or 1.0 
        fused = [ (jid, round((s / top_score) * 100, 2)) for jid, s in fused ]

    return fused


# Section 4 — Candidate fetching
def _build_similarity_expr(
    skills_vec:  list[float],
    work_vec:    list[float] | None,
    project_vec: list[float] | None,
):
    """
    Build a pgvector weighted inner-product expression for ORDER BY.

    Embeddings are L2-normalised so inner product == cosine similarity.
    max_inner_product returns the NEGATIVE dot product, so ORDER BY ASC
    gives highest similarity first — consistent with _cosine_sim in Python.

    Mirrors the same dynamic weights used in _rank_by_semantic.
    """
    has_work = work_vec    is not None
    has_proj = project_vec is not None

    if has_work and has_proj:
        return (
            Job.skill_embedding.max_inner_product(skills_vec)  * 0.50
            + Job.job_embedding.max_inner_product(work_vec)    * 0.30
            + Job.job_embedding.max_inner_product(project_vec) * 0.20
        )
    elif has_work:
        return (
            Job.skill_embedding.max_inner_product(skills_vec) * 0.60
            + Job.job_embedding.max_inner_product(work_vec)   * 0.40
        )
    elif has_proj:
        return (
            Job.skill_embedding.max_inner_product(skills_vec)  * 0.65
            + Job.job_embedding.max_inner_product(project_vec) * 0.35
        )
    else:
        return Job.skill_embedding.max_inner_product(skills_vec)


def _fetch_candidates(
    base_query,
    skills_vec:  list[float],
    work_vec:    list[float] | None,
    project_vec: list[float] | None,
    limit:       int,
    db:          Session,
) -> list[Job]:
    """
    Two-step candidate fetch to avoid the DISTINCT + ORDER BY + joinedload
    subquery bug that causes SQLAlchemy to drop jobs silently.

    Step 1 — fetch job_ids only, ordered by inner product similarity.
             No joinedload here so no DISTINCT interference.
    Step 2 — reload exactly those jobs with locations eagerly loaded.
             No ORDER BY or DISTINCT so no jobs are lost.
    """
    similarity_expr = _build_similarity_expr(skills_vec, work_vec, project_vec)

    # Step 1: get IDs only — clean ordering, no location join interference
    id_rows = (
        base_query
        .with_entities(Job.job_id)
        .order_by(similarity_expr.asc())          
        .limit(limit * CANDIDATE_MULTIPLIER)
        .all()
    )
    candidate_ids = [row.job_id for row in id_rows]

    if not candidate_ids:
        return []

    # Step 2: load full job objects with locations — no ordering, no drops
    return (
        db.query(Job)
        .options(joinedload(Job.locations))
        .filter(Job.job_id.in_(candidate_ids))
        .all()
    )


# Section 5 — Resume resolution (profile mode vs. uploaded file)
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


def _resolve_profile_vectors(
    target_user_id: UUID,
    db: Session,
) -> ResumeVectors | None:
    """
    Load resume vectors from the saved profile.

    Returns None if no saved resume exists (caller falls back to newest-first).
    Resume.resume_text is read directly — it was persisted at upload time as
    skills + work_experience + projects — so hybrid (semantic + BM25) scoring
    is fully available in profile mode with no re-parsing needed.
    """
    saved_resume = (
        db.query(Resume)
        .filter(Resume.user_id == target_user_id)
        .first()
    )
    if not saved_resume:
        return None

    return ResumeVectors(
        skills_vec      = saved_resume.skill_embedding,
        work_vec        = saved_resume.work_embedding,
        project_vec     = saved_resume.project_embedding,
        bm25_query_text = saved_resume.resume_text or "",
    )


def _resolve_uploaded_vectors(
    resume_file:    UploadFile,
    target_user_id: UUID,
) -> ResumeVectors:
    """
    Parse an uploaded resume PDF into vectors + BM25 query text.

    create_resume_embedding returns resume_text as its 1st value so no
    second LLM call or extract_json import is needed here.

    The temp file is written to disk, processed, then deleted regardless
    of success or failure.
    """
    validate_pdf_extension(resume_file)
    validate_file_size(resume_file)

    temp_path = f"temp_{target_user_id}.pdf"
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(resume_file.file, buffer)

        bm25_text, skill_emb, work_emb, project_emb = (
            create_resume_embedding(temp_path)
        )
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

    return ResumeVectors(
        skills_vec      = skill_emb,
        work_vec        = work_emb,
        project_vec     = project_emb,
        bm25_query_text = bm25_text,
    )


# Section 6 — Filter resolution

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


def _resolve_profile_filters(
    target_user_id: UUID,
    db: Session,
) -> JobFilters:
    """
    Pull job filter preferences from the saved JobSeekerProfile.

    Raises 404 if no profile exists.
    """
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

    pref_locs = (
        db.query(JobSeekerPreferredLocation)
        .filter(JobSeekerPreferredLocation.user_id == target_user_id)
        .all()
    )
    location_ids = [pl.location_id for pl in pref_locs] if pref_locs else None

    return JobFilters(
        domain_id    = profile.preferred_domain_id,
        experience   = profile.experience,
        location_ids = location_ids,
    )


# Section 7 — Base query builder

def _apply_hard_filters(db: Session, filters: JobFilters):
    """
    Build a SQLAlchemy query for Job with hard filters applied.
    No joinedload here — locations are loaded separately in _fetch_candidates
    Step 2 to avoid DISTINCT + ORDER BY subquery conflicts.
    Filters are skipped when their value is None.
    """
    query = db.query(Job)

    if filters.domain_id is not None:
        query = query.filter(Job.industry_domain_id == filters.domain_id)

    if filters.experience is not None:
        query = query.filter(Job.min_experience <= filters.experience)

    if filters.location_ids:
        query = (
            query
            .join(Job.locations)
            .filter(Location.id.in_(filters.location_ids))
            .group_by(Job.job_id)
        )

    return query


# Section 8 — Response builders

def _build_hybrid_response(
    candidate_jobs: list[Job],
    vectors:        ResumeVectors,
    limit:          int,
) -> list[RecJobResponse]:
    """
    Run semantic ranking + BM25 ranking → fuse via RRF → return top `limit`.
    """
    semantic_ranking = _rank_by_semantic(
        candidate_jobs,
        vectors.skills_vec,
        vectors.work_vec,
        vectors.project_vec,
    )

    bm25_ranking = (
        _rank_by_bm25(vectors.bm25_query_text, candidate_jobs)
        if vectors.bm25_query_text.strip()
        else semantic_ranking
    )

    fused_scores = _reciprocal_rank_fusion(
        semantic_ranking = semantic_ranking,
        bm25_ranking     = bm25_ranking,
        semantic_weight  = 0.60,
        bm25_weight      = 0.40,
    )

    job_map: dict[UUID, Job] = {job.job_id: job for job in candidate_jobs}

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


def _build_fallback_response(jobs: list[Job]) -> list[RecJobResponse]:
    """Newest-first response when no resume vectors are available."""
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
        for job in jobs
    ]


# Section 9 — Endpoint

@router.post("/jobs", response_model=List[RecJobResponse])
async def get_recommended_jobs(
    use_profile:  bool                 = Form(False),
    domain_id:    Optional[int]        = Query(None),
    location_ids: Optional[List[int]]  = Query(None),
    experience:   Optional[int]        = Query(None),
    resume_file:  Optional[UploadFile] = File(None),
    limit:        int                  = 10,
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

    # 2. Resolve resume vectors ------------------------------------------------
    vectors: ResumeVectors | None = None
    if use_profile:
        vectors = _resolve_profile_vectors(target_user_id, db)
    elif resume_file:
        vectors = _resolve_uploaded_vectors(resume_file, target_user_id)

    # 3. Apply hard filters ----------------------------------------------------
    base_query = _apply_hard_filters(db, filters)

    # 4. Rank and return -------------------------------------------------------
    if vectors is not None:
        candidate_jobs = _fetch_candidates(
            base_query,
            vectors.skills_vec,
            vectors.work_vec,
            vectors.project_vec,
            limit,
            db,                  # passed for Step 2 reload
        )
        if not candidate_jobs:
            return []
        return _build_hybrid_response(candidate_jobs, vectors, limit)

    # Fallback — no resume, return newest jobs passing the hard filters
    fallback_jobs = (
        db.query(Job)
        .options(joinedload(Job.locations))
        .filter(Job.job_id.in_(
            base_query.with_entities(Job.job_id).subquery()
        ))
        .order_by(Job.posted_at.desc())
        .limit(limit)
        .all()
    )
    return _build_fallback_response(fallback_jobs)