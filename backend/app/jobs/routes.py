from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session,joinedload
from datetime import datetime, timezone

from .schemas import JobPostRequest, JobPostResponse,JobResponse,DeleteJobResponse
from app.database import get_db
from app.models import Job, Location, IndustryDomain
from .utils import create_job_embedding
from app.utils import get_current_recruiter
from typing import List
from uuid import UUID


router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.post("/post", response_model=JobPostResponse)
def create_job(
    job: JobPostRequest,
    db: Session = Depends(get_db),
    current_recruiter: dict = Depends(get_current_recruiter)
):

    # Validate industry domain
    domain = db.query(IndustryDomain).filter(
        IndustryDomain.id == job.industry_domain_id
    ).first()

    if not domain:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid industry_domain_id"
        )

    # Validate locations
    locations = db.query(Location).filter(
        Location.id.in_(job.location_ids)
    ).all()

    if len(locations) != len(job.location_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One or more location_ids are invalid"
        )


    try:
        skill_embedding, job_embedding = create_job_embedding(job.job_description)
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Embedding service temporarily unavailable"
        )
   
    new_job = Job(
        job_title=job.job_title,
        company_name=job.company_name,
        industry_domain_id=job.industry_domain_id,
        min_experience=job.min_experience,
        job_description=job.job_description,
        recruiter_id=current_recruiter["user_id"],
        skill_embedding=skill_embedding,
        job_embedding=job_embedding,
        posted_at=datetime.now(timezone.utc)
    )

    # Attach many-to-many locations
    new_job.locations = locations

    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    return new_job


@router.get("/postedjobs", response_model=List[JobResponse])
def get_posted_jobs(
    db: Session = Depends(get_db),
    current_recruiter: dict = Depends(get_current_recruiter)
):

    jobs = (
        db.query(Job)
        .options(joinedload(Job.locations))
        .filter(Job.recruiter_id == current_recruiter["user_id"])
        .order_by(Job.posted_at.desc()) 
        .all()
    )

    return [
        JobResponse(
            job_id=job.job_id,
            job_title=job.job_title,
            company_name=job.company_name,
            locations=[loc.name for loc in job.locations],
            job_description=job.job_description,
            min_experience=job.min_experience
        )
        for job in jobs
    ]

@router.delete("/{job_id}", response_model=DeleteJobResponse)
def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_recruiter: dict = Depends(get_current_recruiter)
):

    job = (
        db.query(Job)
        .filter(
            Job.job_id == job_id,
            Job.recruiter_id == current_recruiter["user_id"]
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    db.delete(job)
    db.commit()

    return DeleteJobResponse(job_id=job_id)


@router.get("/locations")
def get_locations(db: Session = Depends(get_db)):
    return db.query(Location).all()


@router.get("/industry-domains")
def get_industry_domains(db: Session = Depends(get_db)):
    return db.query(IndustryDomain).all()

