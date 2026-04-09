import hashlib
import base64
from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.ALGORITHM)
    return encoded_jwt

def _get_prehashed_password(password: str) -> str:
    """
    To overcome bcrypt's 72-character limit, we pre-hash the password with SHA-256.
    We then base64-encode the digest to make it passlib-compatible.
    """
    sha256_hash = hashlib.sha256(password.encode("utf-8")).digest()
    return base64.b64encode(sha256_hash).decode("utf-8")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    prehashed = _get_prehashed_password(plain_password)
    return pwd_context.verify(prehashed, hashed_password)

def get_password_hash(password: str) -> str:
    prehashed = _get_prehashed_password(password)
    return pwd_context.hash(prehashed)
