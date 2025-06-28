from uuid import uuid4
from typing import Optional

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta, timezone
from jose import ExpiredSignatureError, jwt, JWTError

# from passlib.context import CryptContext
from src.app.config.config import settings
from src.app.core.database import get_db
from sqlalchemy.orm import Session
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerifyMismatchError

from src.app.domain.auth.crud import auth_crud as crud

pwd_context = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
ALGORITHM = "HS256"


def create_access_token(
    subject: str,
    expires_delta: Optional[int] = None,
    key: str = settings.SECRET_KEY,
    issuer: str = "codeground",
    audience: Optional[str] = "codeground",
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=expires_delta or settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": subject,  # subject (ex: user email or id)
        "iat": int(now.timestamp()),  # issued at (timestamp)
        "exp": int(expire.timestamp()),  # expiration (timestamp)
        "iss": issuer,  # issuer
        "aud": audience,
        "jti": str(uuid4()),
    }
    encoded_jwt = jwt.encode(payload, key, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False
    except InvalidHash:
        raise HTTPException(status_code=400, detail="Invalid hash format.")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def decode_token(token: str, key: str = settings.SECRET_KEY, issuer: str = "codeground", audience: str = "codeground"):
    try:
        payload = jwt.decode(token, key, algorithms=[ALGORITHM], audience=audience, issuer=issuer)
        return payload.get("sub")
    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token is expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        email = decode_token(token)
        user = await crud.get_user_by_email(db, email=email)
        if user is None:
            raise HTTPException(status_code=401, detail="User is None")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
