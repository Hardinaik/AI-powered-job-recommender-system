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
    limit: int = 20, # Increased default limit for better ranking pool
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    target_user_id = UUID(current_user["user_id"])
    skills_vec = None
    summary_vec = None

    # -------- 1. PRE-VALIDATION --------
    if resume_file and use_saved_resume:
        raise HTTPException(status_code=400, detail="Provide either file or use_saved_resume.")

    # -------- 2. VECTOR ACQUISITION --------
    if resume_file:
        validate_pdf_extension(resume_file)
        validate_file_size(resume_file)
        temp_path = f"temp_{target_user_id}.pdf"
        try:
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(resume_file.file, buffer)
            
            s_emb, w_emb, cleaned_text = create_resume_embedding(temp_path)
            
            # Update or Create Resume entry
            existing = db.query(Resume).filter(Resume.user_id == target_user_id).first()
            if existing:
                existing.resume_text, existing.skill_embedding, existing.resume_embedding = cleaned_text, s_emb, w_emb
                existing.updated_at = func.now()
            else:
                db.add(Resume(user_id=target_user_id, resume_text=cleaned_text, skill_embedding=s_emb, resume_embedding=w_emb))
            
            db.commit()
            skills_vec, summary_vec = s_emb, w_emb
        finally:
            if os.path.exists(temp_path): os.remove(temp_path)

    elif use_saved_resume:
        saved = db.query(Resume).filter(Resume.user_id == target_user_id).first()
        if not saved:
            raise HTTPException(status_code=404, detail="No saved resume found.")
        skills_vec, summary_vec = saved.skill_embedding, saved.resume_embedding

    # -------- 3. BUILD QUERY & SORTING --------
    # Base query with joinedload for performance
    query = db.query(Job).options(joinedload(Job.locations))

    # Apply hard filters (Domain, Experience, Location)
    if domain_id:
        query = query.filter(Job.industry_domain_id == domain_id)
    if experience is not None:
        query = query.filter(Job.min_experience <= experience)
    if location_id:
        query = query.join(Job.locations).filter(Location.id == location_id).distinct()

    # -------- 4. EXECUTION BASED ON RANKING TYPE --------
    if skills_vec is not None and summary_vec is not None:
        
        # Combined distance: 60% skills similarity, 40% general content similarity
        distance_expr = (
            Job.skill_embedding.cosine_distance(skills_vec) * 0.6 +
            Job.job_embedding.cosine_distance(summary_vec) * 0.4
        )
        score_expr = (1 - distance_expr) * 100

        # We only order by distance here to ensure match score takes priority
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
            ) for row in results
        ]

    else:
        # FALLBACK MODE: Sort by newest jobs if no resume is used
        jobs = query.order_by(Job.posted_at.desc()).limit(limit).all()
        return [
            RecJobResponse(
                job_id=job.job_id,
                job_title=job.job_title,
                locations=[loc.name for loc in job.locations],
                job_description=job.job_description,
                min_experience=job.min_experience,
                company_name=job.company_name,
                match_score=0.0
            ) for job in jobs
        ]