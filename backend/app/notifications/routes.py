from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Job, User, Resume, JobSeekerProfile
from app.utils import get_current_jobseeker
from app.notifications.schemas import ApplicationNotifyForm, ApplicationPrefillResponse
from app.services.email_services import (
    send_recruiter_application_email,
    send_jobseeker_confirmation_email,
)

router = APIRouter(prefix="/notifications/jobs", tags=["Notifications"])


# ─────────────────────────────────────────────────────────────────────────────
# GET /jobs/{job_id}/apply/prefill
# Called when the Apply modal opens — returns DB values to pre-fill the form
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{job_id}/apply/prefill",
    response_model=ApplicationPrefillResponse,
    summary="Pre-fill apply form with user's existing profile data",
)
async def get_apply_prefill(
    job_id:       UUID,
    db:           Session = Depends(get_db),
    current_user: dict    = Depends(get_current_jobseeker),
):
    """
    Returns whatever data exists in the DB for the current user.
    Optional fields (phone, experience, resume_url) may come back as
    None / 0 if the user hasn't filled their profile yet — frontend
    should show empty input fields in that case.
    """
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    seeker: User = db.query(User).filter(
        User.user_id == current_user["user_id"]
    ).first()

    profile: JobSeekerProfile | None = db.query(JobSeekerProfile).filter(
        JobSeekerProfile.user_id == current_user["user_id"]
    ).first()

    resume: Resume | None = db.query(Resume).filter(
        Resume.user_id == current_user["user_id"]
    ).first()

    return ApplicationPrefillResponse(
        name       = seeker.fullname,
        email      = seeker.email,
        phone      = seeker.phone,                             # None if not set
        experience = profile.experience if profile else 0,     # 0 if no profile row
        resume_url = resume.resume_url  if resume  else None,  # None if no resume row
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /jobs/{job_id}/apply/notify
# Call this AFTER the DB apply API succeeds — sends both emails
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/{job_id}/apply/notify",
    status_code=202,
    summary="Send application emails to recruiter and jobseeker",
)
async def notify_application(
    job_id:           UUID,
    form:             ApplicationNotifyForm,
    background_tasks: BackgroundTasks,             
    db:               Session = Depends(get_db),
):
    """
    Accepts the fully filled form (pre-filled values + user edits).
    Sends:
      1. Recruiter email — full applicant details
      2. Jobseeker email — confirmation card
    """
    job: Job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    recruiter: User = db.query(User).filter(
        User.user_id == job.recruiter_id
    ).first()
    if not recruiter:
        raise HTTPException(status_code=404, detail="Recruiter not found")

    company    = job.company_name or "the company"
    job_id_str = str(job_id)

    # Replace the two awaited calls with background task registration
    background_tasks.add_task(
        send_recruiter_application_email,
        recruiter_email = recruiter.email,
        recruiter_name  = recruiter.fullname,
        job_title       = job.job_title,
        company_name    = company,
        job_id          = job_id_str,
        applicant_name  = form.name,
        applicant_email = form.email,
        applicant_phone = form.phone,
        experience      = form.experience,
        resume_url      = form.resume_url,
        linkedin        = form.linkedin,
        why_interested  = form.why_interested,
    )

    background_tasks.add_task(
        send_jobseeker_confirmation_email,
        applicant_email = form.email,
        applicant_name  = form.name,
        job_title       = job.job_title,
        company_name    = company,
        job_id          = job_id_str,
    )

    return {"detail": "Application received. Emails are being sent."}