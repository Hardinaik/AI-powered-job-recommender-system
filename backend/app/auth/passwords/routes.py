from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta,timezone

from app.limiter import limiter
from app.config import settings
from app.database import get_db
from app.models import User, PasswordResetToken, RefreshToken
from app.utils import hash_password
from .schemas import ForgotPasswordRequest, ResetPasswordRequest
from .utils import _create_reset_token, _hash_token, _verify_reset_token
from app.services.email_services import send_reset_email


router = APIRouter(prefix="/auth/passwords", tags=["Reset Password"])


@router.post("/forgot-password")
@limiter.limit("2/minute")
async def forgot_password(
    request: Request,
    body: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == body.email).first()

    # SECURITY: same response whether email exists or not (prevents enumeration)
    if not user:
        return {"message": "If this email is registered, a reset link has been sent."}

    # Invalidate all previous unused reset tokens for this user
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.user_id,
        PasswordResetToken.used == False,
    ).delete()

    raw_token   = _create_reset_token(str(user.user_id))
    token_record = PasswordResetToken(
        user_id    = user.user_id,
        token_hash = _hash_token(raw_token),
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    )
    db.add(token_record)
    db.commit()

    await send_reset_email(user.email, raw_token)
    return {"message": "If this email is registered, a reset link has been sent."}


@router.post("/reset-password")
@limiter.limit("2/minute")
async def reset_password(
    request: Request,
    body: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    # 1. Verify JWT signature + expiry
    user_id = _verify_reset_token(body.token)

    # 2. Check token exists in DB — unused and not expired
    token_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == _hash_token(body.token),
        PasswordResetToken.user_id    == user_id,
        PasswordResetToken.used       == False,
        PasswordResetToken.expires_at >  datetime.now(timezone.utc),
    ).first()

    if not token_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already used reset link"
        )

    # 3. Update password
    user = db.query(User).filter(User.user_id == user_id).first()
    user.password_hash = hash_password(body.new_password)

    # 4. Mark reset token as used
    token_record.used = True

    # 5. Revoke ALL active refresh tokens for this user
    #    If account was compromised, this kills every existing session
    db.query(RefreshToken).filter(
        RefreshToken.user_id    == user_id,
        RefreshToken.is_revoked == False,
    ).update({"is_revoked": True})

    db.commit()

    return {"message": "Password updated successfully. Please log in again."}