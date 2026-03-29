import os
import shutil
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import Job, Location, Resume, JobSeekerProfile, JobSeekerPreferredLocation
from .schemas import RecJobResponse
from app.resume.utils import (
    validate_pdf_extension,
    validate_file_size,
    create_resume_embedding
)
from app.utils import get_current_jobseeker

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/jobs", response_model=List[RecJobResponse])
async def get_recommended_jobs(
    # --- Mode switch ---
    use_profile: bool = Form(False),  # True = "Recommend using profile" checkbox

    # --- Manual filter params (only used when use_profile=False) ---
    domain_id: Optional[int] = Query(None),
    location_ids: Optional[List[int]] = Query(None),  # multi-select: ?location_ids=1&location_ids=2
    experience: Optional[int] = Query(None),
    resume_file: Optional[UploadFile] = File(None),  # optional scoring boost in manual mode

    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    target_user_id = UUID(current_user["user_id"])

    skills_vec = None
    work_vec = None
    project_vec = None

    # ================================================================
    # MODE 1 — PROFILE-BASED RECOMMENDATION (checkbox ON)
    # ================================================================
    if use_profile:
        # --- Pull filter values from JobSeekerProfile ---
        profile = (
            db.query(JobSeekerProfile)
            .filter(JobSeekerProfile.user_id == target_user_id)
            .first()
        )
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="No jobseeker profile found. Please complete your profile first."
            )

        # Use whatever is available — missing fields simply won't filter
        domain_id = profile.preferred_domain_id    # None → filter skipped
        experience = profile.experience             # None → filter skipped

        # Pull ALL preferred locations from profile (mirrors multi-select behaviour)
        pref_locs = (
            db.query(JobSeekerPreferredLocation)
            .filter(JobSeekerPreferredLocation.user_id == target_user_id)
            .all()
        )
        location_ids = [pl.location_id for pl in pref_locs] if pref_locs else None

        # --- Pull saved resume embeddings for vector scoring ---
        saved_resume = (
            db.query(Resume)
            .filter(Resume.user_id == target_user_id)
            .first()
        )
        if saved_resume:
            skills_vec = saved_resume.skill_embedding
            work_vec = saved_resume.work_embedding
            project_vec = saved_resume.project_embedding
        # If no saved resume — filters still apply, scoring falls back to newest-first

    # ================================================================
    # MODE 2 — MANUAL FILTERS (checkbox OFF)
    # ================================================================
    else:
        # domain_id, location_ids, experience come directly from Query params above.
        # resume_file is optional — used for scoring only, never saved to DB.
        if resume_file:
            validate_pdf_extension(resume_file)
            validate_file_size(resume_file)

            temp_path = f"temp_{target_user_id}.pdf"
            try:
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(resume_file.file, buffer)

                skill_emb, work_emb, project_emb = create_resume_embedding(temp_path)
                skills_vec, work_vec, project_vec = skill_emb, work_emb, project_emb
                # NOT saved to DB — manual mode is a one-shot query

            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    # ================================================================
    # BUILD BASE QUERY WITH HARD FILTERS (shared by both modes)
    # ================================================================
    query = db.query(Job).options(joinedload(Job.locations))

    if domain_id is not None:
        query = query.filter(Job.industry_domain_id == domain_id)

    if experience is not None:
        query = query.filter(Job.min_experience <= experience)

    if location_ids:
        # Jobs that have AT LEAST ONE location matching any of the selected ids
        query = (
            query.join(Job.locations)
            .filter(Location.id.in_(location_ids))
            .distinct()
        )

    # ================================================================
    # RANKING
    # ================================================================
    all_vecs_available = (
        skills_vec is not None
        and work_vec is not None
        and project_vec is not None
    )

    if all_vecs_available:
        # Weighted cosine distance:
        #   50% — skill match        (resume skills    ↔ job skills)
        #   30% — work-exp match     (work summary     ↔ job summary)
        #   20% — project match      (project summary  ↔ job summary)
        distance_expr = (
            Job.skill_embedding.cosine_distance(skills_vec) * 0.50
            + Job.job_embedding.cosine_distance(work_vec) * 0.30
            + Job.job_embedding.cosine_distance(project_vec) * 0.20
        )
        score_expr = (1 - distance_expr) * 100

        results = (
            query
            .add_columns(score_expr.label("calculated_score"))
            .order_by(distance_expr.asc())
            .limit(limit)
            .all()
        )

        return [
            RecJobResponse(
                job_id=row.Job.job_id,
                job_title=row.Job.job_title,
                locations=[loc.name for loc in row.Job.locations],
                job_description=row.Job.job_description,
                min_experience=row.Job.min_experience,
                company_name=row.Job.company_name,
                match_score=round(max(0.0, float(row.calculated_score)), 2),
            )
            for row in results
        ]

    else:
        # FALLBACK — no vectors available, return newest jobs that pass filters
        jobs = query.order_by(Job.posted_at.desc()).limit(limit).all()
        return [
            RecJobResponse(
                job_id=job.job_id,
                job_title=job.job_title,
                locations=[loc.name for loc in job.locations],
                job_description=job.job_description,
                min_experience=job.min_experience,
                company_name=job.company_name,
                match_score=0.0,
            )
            for job in jobs
        ]