from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.utils import get_current_jobseeker
from typing import List
from uuid import UUID
from .schemas import SaveJobResponse, JobResponse,ShowCompanyDetails
from app.models import Job, SavedJob, Application,RecruiterProfile
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/applications", tags=["Applications"])

# --- ACTIONS (POST) ---

@router.post("/jobs/{job_id}/save", response_model=SaveJobResponse)
def save_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    saved_job = SavedJob(job_seeker_id=current_user["user_id"], job_id=job_id)
    try:
        db.add(saved_job)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Job already saved")

    return SaveJobResponse(job_id=job_id, message="Job saved successfully")


@router.delete("/jobs/{job_id}/unsave", response_model=SaveJobResponse)
def unsave_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    saved_job = db.query(SavedJob).filter(
        SavedJob.job_seeker_id == current_user["user_id"],
        SavedJob.job_id == job_id
    ).first()

    if not saved_job:
        raise HTTPException(status_code=404, detail="Job not saved")

    try:
        db.delete(saved_job)
        db.commit()
    except:
        db.rollback()
        raise HTTPException(status_code=500, detail="Error while unsaving job")

    return SaveJobResponse(
        job_id=job_id,
        message="Job unsaved successfully"
    )

@router.post("/jobs/{job_id}/apply", response_model=UUID)
def apply_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    application = Application(job_seeker_id=current_user["user_id"], job_id=job_id)
    try:
        db.add(application)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Already applied to this job")

    return job_id


# --- STATE PERSISTENCE (GET IDs ONLY) ---
# Use these for highlighting buttons on the main list

@router.get("/saved-jobs/ids", response_model=List[UUID])
def get_saved_job_ids(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    saved_jobs = db.query(SavedJob.job_id).filter(
        SavedJob.job_seeker_id == current_user["user_id"]
    ).all()
    return [job.job_id for job in saved_jobs]

@router.get("/applied-jobs/ids", response_model=List[UUID])
def get_applied_job_ids(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    applied_jobs = db.query(Application.job_id).filter(
        Application.job_seeker_id == current_user["user_id"]
    ).all()
    return [job.job_id for job in applied_jobs]


# --- VIEW CONTENT (GET FULL DETAILS) ---
# Use these when the user clicks the "Saved" or "Applied" tabs

@router.get("/saved-jobs/details", response_model=List[JobResponse])
def get_saved_jobs_details(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    jobs = (
        db.query(Job)
        .join(SavedJob, SavedJob.job_id == Job.job_id)
        .filter(SavedJob.job_seeker_id == current_user["user_id"])
        .options(joinedload(Job.locations))
        .all()
    )
    return [
        JobResponse(
            job_id=job.job_id,
            job_title=job.job_title,
            locations=[loc.name for loc in job.locations],
            job_description=job.job_description,
            min_experience=job.min_experience,
            company_name=job.company_name
        ) for job in jobs
    ]

@router.get("/applied-jobs/details", response_model=List[JobResponse])
def get_applied_jobs_details(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    jobs = (
        db.query(Job)
        .join(Application, Application.job_id == Job.job_id)
        .filter(Application.job_seeker_id == current_user["user_id"])
        .options(joinedload(Job.locations))
        .all()
    )
    return [
        JobResponse(
            job_id=job.job_id,
            job_title=job.job_title,
            locations=[loc.name for loc in job.locations],
            job_description=job.job_description,
            min_experience=job.min_experience,
            company_name=job.company_name
        ) for job in jobs
    ]

@router.get("/jobs/{job_id}/company-details", response_model=ShowCompanyDetails)
def get_company_details(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_jobseeker)
):
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    profile = db.query(RecruiterProfile).filter(
        RecruiterProfile.user_id == job.recruiter_id
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Company details not found")

    return ShowCompanyDetails(
        company_name=profile.company_name,
        website=profile.website,
        linkedin=profile.linkedin,
        description=profile.description
    )