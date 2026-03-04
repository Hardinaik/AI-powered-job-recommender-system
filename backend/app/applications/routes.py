from fastapi import APIRouter, Depends, HTTPException,status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.utils import get_current_jobseeker
from typing import List
from uuid import UUID
from app.schemas import SaveJobResponse


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


