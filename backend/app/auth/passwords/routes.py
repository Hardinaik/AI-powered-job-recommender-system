from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.config import settings
from app.models import User, PasswordResetToken
from .schemas import ForgotPasswordRequest, ResetPasswordRequest
from .utils import _create_reset_token, _hash_token, _verify_reset_token
from app.services.email_services import send_reset_email
from app.database import get_db
from app.utils import hash_password 

router = APIRouter(prefix="/auth/passwords", tags=["Reset Password"])


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()

    # SECURITY: same response whether email exists or not (prevents enumeration)
    if not user:
        raise HTTPException(status_code=404, detail="No account found with this email address.")
    # Invalidate all previous unused tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,  
        PasswordResetToken.used == False,
    ).delete()

    raw_token = _create_reset_token(str(user.user_id)) 
    token_record = PasswordResetToken(
        user_id=user.user_id,                         
        token_hash=_hash_token(raw_token),
        expires_at=datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(token_record)
    db.commit()

    await send_reset_email(user.email, raw_token)
    return {"message": "If this email is registered, a reset link has been sent."}


@router.post("/reset-password")
async def reset_password(body: ResetPasswordRequest, db: Session = Depends(get_db)):
    # 1. Verify JWT signature + expiry
    user_id = _verify_reset_token(body.token)

    # 2. Check token exists in DB, unused, and not expired
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == _hash_token(body.token),
        PasswordResetToken.user_id == user_id,
        PasswordResetToken.used == False,
        PasswordResetToken.expires_at > datetime.utcnow(),
    ).first()

    if not token_record:
        raise HTTPException(status_code=400, detail="Invalid or already used reset link")

  
    # 4. Hash using your existing utility (same as used during registration)
    new_hashed = hash_password(body.new_password)  

    # 5. Update password + mark token used — both in one transaction
    user = db.query(User).filter(User.user_id == user_id).first()  
    user.password_hash = new_hashed  
    token_record.used = True
    db.commit()

    return {"message": "Password updated successfully"}