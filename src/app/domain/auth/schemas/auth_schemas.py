from typing import Optional
from pydantic import BaseModel
from src.app.config.config import settings


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


class UserSignupRequest(BaseModel):
    email: str
    username: str
    password: str
    nickname: str


class UserSignupResponse(BaseModel):
    email: str
    username: str
    nickname: str

    model_config = {"from_attributes": True}


class UserDto(BaseModel):
    email: str
    username: str
    nickname: str

    model_config = {"from_attributes": True}
