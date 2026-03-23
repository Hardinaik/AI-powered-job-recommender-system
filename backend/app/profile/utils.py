from fastapi import Depends, HTTPException
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