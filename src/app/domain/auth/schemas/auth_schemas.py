from typing import Optional
from pydantic import BaseModel, constr, EmailStr
from src.app.config.config import settings


class SignupRequest(BaseModel):
    email: EmailStr
    username: str
    password: constr(min_length=8, max_length=20)
    nickname: str
    use_lang: str  # 예: Python, Java, C, C++
    tier_choice: str  # 예: 브론즈, 실버, 골드, 플래티넘 이상, 티어 없음


class SignupResponse(BaseModel):
    email: str
    username: str
    nickname: str

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60


class LoginUserDto(BaseModel):
    email: str
    username: str
    nickname: str

    model_config = {"from_attributes": True}
