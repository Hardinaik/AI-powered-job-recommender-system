from jose import JWTError, jwt
import hashlib
from datetime import datetime, timedelta
from app.config import settings
from fastapi import HTTPException

def _hash_token(token: str) -> str:
    """SHA-256 hash — we never store the raw token in DB."""
    return hashlib.sha256(token.encode()).hexdigest()

def _create_reset_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "exp": expire, "type": "password_reset"},
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

def _verify_reset_token(token: str) -> str:
    """Returns user_id or raises HTTPException."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "password_reset":
            raise ValueError("Wrong token type")
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
