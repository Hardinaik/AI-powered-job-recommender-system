import os
import shutil

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.utils import get_current_jobseeker
from app.models import Resume, User
from .utils import (
    create_resume_embedding,
    validate_file_size,
    validate_pdf_extension,
)

router = APIRouter(prefix="/resume", tags=["Resume"])

UPLOAD_DIR = "uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_jobseeker),
):
    validate_pdf_extension(file)
    validate_file_size(file)

    user_id = current_user["user_id"]

    existing_resume: Resume | None = (
        db.query(Resume).filter(Resume.user_id == user_id).first()
    )

    if existing_resume and existing_resume.resume_url:
        old_path = existing_resume.resume_url
        if os.path.exists(old_path):
            os.remove(old_path)

    file_path = Path(UPLOAD_DIR) / f"{user_id}.pdf"
    

    file.file.seek(0)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        resume_text,skill_embedding, work_embedding, project_embedding = create_resume_embedding(file_path)
    except Exception as e:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=422,
            detail=f"Resume processing failed: {str(e)}",
        )

    if existing_resume:
        existing_resume.resume_url = file_path
        existing_resume.resume_text=resume_text
        existing_resume.skill_embedding = skill_embedding
        existing_resume.work_embedding = work_embedding      
        existing_resume.project_embedding = project_embedding
    else:
        new_resume = Resume(
            user_id=user_id,
            resume_url=file_path.as_posix(),
            resume_text=resume_text,
            skill_embedding=skill_embedding,
            work_embedding=work_embedding,
            project_embedding=project_embedding,
        )
        db.add(new_resume)

    db.commit()

    return {
        "message": "Resume uploaded successfully.",
        "resume_url": "/resume/view",
    }


@router.delete("/delete", status_code=200)
async def delete_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_jobseeker),
):
    user_id = current_user["user_id"]

    existing_resume: Resume | None = (
        db.query(Resume).filter(Resume.user_id == user_id).first()
    )

    if not existing_resume:
        raise HTTPException(
            status_code=404,
            detail="No resume found for this user.",
        )

    if existing_resume.resume_url and os.path.exists(existing_resume.resume_url):
        os.remove(existing_resume.resume_url)

    db.delete(existing_resume)
    db.commit()

    return {"message": "Resume deleted successfully."}


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_resume_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_jobseeker),
):
    user_id = current_user["user_id"]

    resume: Resume | None = (
        db.query(Resume).filter(Resume.user_id == user_id).first()
    )

    if not resume or not resume.resume_url:
        return {"has_resume": False, "resume_url": None}

    return {
        "has_resume": True,
        "resume_url": "/resume/view",
    }


@router.get("/view", status_code=status.HTTP_200_OK)
async def view_resume(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_jobseeker),
):
    user_id = current_user["user_id"]

    resume: Resume | None = (
        db.query(Resume).filter(Resume.user_id == user_id).first()
    )

    if not resume or not resume.resume_url:
        raise HTTPException(
            status_code=404,
            detail="No resume found for this user.",
        )

    file_path = resume.resume_url

    # ── Path traversal guard ───────────────────────────────────────
    safe_dir = os.path.realpath(UPLOAD_DIR)
    real_path = os.path.realpath(file_path)

    if not real_path.startswith(safe_dir):
        raise HTTPException(status_code=403, detail="Access denied.")

    if not os.path.exists(real_path):
        raise HTTPException(
            status_code=404,
            detail="Resume file not found on server. Please re-upload.",
        )

    return FileResponse(
        path=real_path,
        media_type="application/pdf",
        filename=f"resume_{user_id}.pdf",
        headers={"Content-Disposition": "inline"},
    )