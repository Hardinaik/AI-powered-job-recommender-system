from datetime import datetime,timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session


from app.limiter import limiter
from app.database import get_db
from app.models import User, RefreshToken
from app.config import settings
from .schemas import SignupRequest, LoginRequest
from app.utils import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
)


router = APIRouter(prefix="/auth", tags=["Auth"])


# ============================================================
#  Helper — issues both tokens, sets cookie, returns response
# ============================================================
def _issue_tokens(user: User, request: Request, db: Session) -> JSONResponse:
    """
    Creates access + refresh token, persists refresh token in DB,
    sets HttpOnly cookie, returns JSONResponse with access token.
    Called on both signup and login.
    """
    # Access token (short-lived JWT)
    access_token = create_access_token(
        data={"sub": str(user.user_id), "role": user.user_role}
    )

    # Refresh token (opaque, stored hashed in DB)
    raw_token, token_hash, expires_at = create_refresh_token()

    db_token = RefreshToken(
        user_id    = user.user_id,
        token_hash = token_hash,
        expires_at = expires_at,
        user_agent = request.headers.get("user-agent"),
        ip_address = request.client.host if request.client else None,
    )
    db.add(db_token)
    db.commit()

    # Build response — access token in body, refresh token in HttpOnly cookie
    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type":   "bearer",
            "role":         user.user_role,
        }
    )
    
    # routes.py
    response.set_cookie(
        key      = "refresh_token",
        value    = raw_token,
        httponly = True,
        secure   = settings.IS_PRODUCTION,
        samesite = "lax",
        max_age  = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return response


# ============================================================
#  Signup
# ============================================================
@router.post("/signup", status_code=status.HTTP_201_CREATED)
@limiter.limit("2/minute")
def signup(request: Request, data: SignupRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    user = User(
        fullname      = data.fullname,
        email         = data.email,
        password_hash = hash_password(data.password),
        user_role     = data.user_role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return _issue_tokens(user, request, db)


# ============================================================
#  Login
# ============================================================
@router.post("/login")
@limiter.limit("2/minute")
def login(request: Request, data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == data.email).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password"
        )

    return _issue_tokens(user, request, db)


# ============================================================
#  Refresh
# ============================================================
@router.post("/refresh")
def refresh(request: Request, db: Session = Depends(get_db)):
    raw_token = request.cookies.get("refresh_token")
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token"
        )

    token_hash = hash_refresh_token(raw_token)

    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == token_hash
    ).first()

    if (
        not db_token
        or db_token.is_revoked
        or db_token.expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )

    # Rotate — revoke old token, issue new one
    db_token.is_revoked = True

    raw_new, hash_new, expires_new = create_refresh_token()
    db.add(RefreshToken(
        user_id    = db_token.user_id,
        token_hash = hash_new,
        expires_at = expires_new,
        user_agent = request.headers.get("user-agent"),
        ip_address = request.client.host if request.client else None,
    ))
    db.commit()

    # New access token
    access_token = create_access_token({
        "sub":  str(db_token.user_id),
        "role": db_token.user.user_role,
    })

    response = JSONResponse(content={"access_token": access_token})
    response.set_cookie(
        key      = "refresh_token",
        value    = raw_new,
        httponly = True,
        secure   = True,
        samesite = "strict",
        max_age  = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )
    return response


# ============================================================
#  Logout
# ============================================================
@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    raw_token = request.cookies.get("refresh_token")

    if raw_token:
        token_hash = hash_refresh_token(raw_token)
        db_token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash
        ).first()
        if db_token:
            db_token.is_revoked = True
            db.commit()

    response = JSONResponse(content={"detail": "Logged out"})
    response.delete_cookie("refresh_token")
    return response