import secrets
import hashlib
from datetime import datetime, timedelta,timezone

from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from app.config import settings


SECRET_KEY                  = settings.SECRET_KEY
ALGORITHM                   = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS   = settings.REFRESH_TOKEN_EXPIRE_DAYS 
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security    = HTTPBearer()


# ============================================================
#  Password
# ============================================================
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================
#  Access token  (JWT, lives in memory on client)
# ============================================================
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ============================================================
#  Refresh token  (opaque random string, lives in HttpOnly cookie)
# ============================================================
def create_refresh_token() -> tuple[str, str, datetime]:
    """
    Returns:
        raw_token  - send this to the client inside an HttpOnly cookie
        token_hash - store this in the DB (never store raw)
        expires_at - store this in the DB for expiry checks
    """
    raw_token  = secrets.token_urlsafe(64)       # cryptographically secure random string
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return raw_token, token_hash, expires_at


def hash_refresh_token(raw_token: str) -> str:
    """Hash an incoming raw token to look it up in the DB."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ============================================================
#  Get current user from access token
# ============================================================
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials

    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id  = payload.get("sub")
        role     = payload.get("role")

        if user_id is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )

        return {"user_id": user_id, "role": role}

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


# ============================================================
#  Role guards
# ============================================================
def get_current_recruiter(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "recruiter":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a recruiter"
        )
    return current_user


def get_current_jobseeker(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "jobseeker":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not a jobseeker"
        )
    return current_user


# ============================================================
#  BM_25 Tokens function
# ============================================================


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    text = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in text)
    return [t for t in text.split() if len(t) > 1]