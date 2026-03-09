from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.utils import get_current_jobseeker
from typing import List
from uuid import UUID
from app.schemas import SaveJobResponse
from app.models import Job,SavedJob,Application
from sqlalchemy.exc import IntegrityError


router = APIRouter(prefix="/applications", tags=["Applications"])

@router.post("/jobs/{job_id}/save", response_model=SaveJobResponse)
def save_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    saved_job = SavedJob(
        job_seeker_id=current_user["user_id"],
        job_id=job_id
    )

    try:
        db.add(saved_job)
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Job already saved"
        )

    return SaveJobResponse(
        job_id=job_id,
        message="Job saved successfully"
    )


@router.get("/saved-jobs", response_model=List[UUID])
def get_saved_jobs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):

    saved_jobs = db.query(SavedJob.job_id).filter(
        SavedJob.job_seeker_id == current_user["user_id"]
    ).all()

    return [job.job_id for job in saved_jobs]

@router.post("/job/{job_id}/apply", response_model=UUID)
def apply_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):

    job = db.query(Job).filter(Job.job_id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found"
        )

    application = Application(
        job_seeker_id=current_user["user_id"],
        job_id=job_id
    )

    try:
        db.add(application)
        db.commit()
        db.refresh(application)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already applied to this job"
        )

    return job_id

@router.get("/applied-jobs", response_model=list[UUID])
def get_applied_jobs(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):

    jobs = (
        db.query(Application.job_id)
        .filter(Application.job_seeker_id == current_user["user_id"])
        .all()
    )

    return [job.job_id for job in jobs]