import os
from fastapi import Depends,UploadFile, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from app.utils import get_current_user


def get_current_user_obj(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}
MAX_IMAGE_SIZE_MB = 5
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024


# ─── Validators ────────────────────────────────────────────────────────────────

def validate_image_extension(file: UploadFile):
    ext = os.path.splitext(file.filename)[-1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{ext}'. Allowed: jpg, jpeg, png.",
        )
    return ext  


async def validate_image_size(file: UploadFile):
    file.file.seek(0, 2)          
    size = file.file.tell()
    file.file.seek(0)             
    if size > MAX_IMAGE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum allowed size is {MAX_IMAGE_SIZE_MB} MB.",
        )
