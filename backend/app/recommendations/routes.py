import os
import shutil
from uuid import UUID
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.database import get_db
from app.models import Job, Location, User, Resume
from app.schemas import RecJobResponse
from .utils import (
    validate_pdf_extension,
    validate_file_size,
    create_resume_embedding
)
from app.utils import get_current_jobseeker

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


@router.post("/jobs", response_model=List[RecJobResponse])
async def get_recommended_jobs(
    domain_id: Optional[int] = Query(None),
    location_id: Optional[int] = Query(None),
    experience: Optional[int] = Query(None),
    use_saved_resume: bool = Form(False),
    resume_file: Optional[UploadFile] = File(None),
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_jobseeker)
):

    target_user_id = UUID(current_user["user_id"])

    skills_vec = None
    summary_vec = None

    limit = min(limit, 50)

    if resume_file and use_saved_resume:
        raise HTTPException(
            status_code=400,
            detail="Provide either resume_file or use_saved_resume, not both."
        )

    # -------- PROCESS NEW RESUME --------
    if resume_file:
        validate_pdf_extension(resume_file)
        validate_file_size(resume_file)

        temp_path = f"temp_{target_user_id}.pdf"

        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(resume_file.file, buffer)

            s_emb, w_emb, cleaned_text = create_resume_embedding(temp_path)

            existing_resume = (
                db.query(Resume)
                .filter(Resume.user_id == target_user_id)
                .first()
            )

            if existing_resume:
                existing_resume.resume_text = cleaned_text
                existing_resume.skill_embedding = s_emb
                existing_resume.resume_embedding = w_emb
                existing_resume.updated_at = func.now()
            else:
                new_resume = Resume(
                    user_id=target_user_id,
                    resume_text=cleaned_text,
                    skill_embedding=s_emb,
                    resume_embedding=w_emb
                )
                db.add(new_resume)

            db.commit()

            skills_vec = s_emb
            summary_vec = w_emb

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    # -------- USE SAVED RESUME --------
    elif use_saved_resume:

        saved = (
            db.query(Resume)
            .filter(Resume.user_id == target_user_id)
            .first()
        )

        if not saved:
            raise HTTPException(
                status_code=404,
                detail="No saved resume found. Please upload one."
            )

        skills_vec = saved.skill_embedding
        summary_vec = saved.resume_embedding

    # -------- BUILD JOB QUERY --------
    query = db.query(Job).options(joinedload(Job.locations))

    if domain_id is not None:
        query = query.filter(Job.industry_domain_id == domain_id)

    if experience is not None:
        query = query.filter(Job.min_experience <= experience)

    if location_id is not None:
        query = (
            query.join(Job.locations)
            .filter(Location.id == location_id)
            .distinct()
        )

    query = query.order_by(Job.posted_at.desc())

    # -------- VECTOR RANKING --------
    if skills_vec is not None and summary_vec is not None:

        distance_expr = (
            Job.skill_embedding.cosine_distance(skills_vec) * 0.6 +
            Job.job_embedding.cosine_distance(summary_vec) * 0.4
        )

        score_expr = (1 - distance_expr) * 100

        results = (
            query.add_columns(score_expr.label("calculated_score"))
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
                match_score=round(max(0.0, float(row.calculated_score)), 2)
            )
            for row in results
        ]

    # -------- FALLBACK (NO RESUME) --------
    jobs = query.limit(limit).all()

    return [
        RecJobResponse(
            job_id=job.job_id,
            job_title=job.job_title,
            locations=[loc.name for loc in job.locations],
            job_description=job.job_description,
            min_experience=job.min_experience,
            company_name=job.company_name,
            match_score=0.0
        )
        for job in jobs
    ]