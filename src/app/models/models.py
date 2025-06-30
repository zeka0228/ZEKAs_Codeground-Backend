from src.app.core.database import Base
from sqlalchemy import Column, DateTime, Integer, String, func, Text, Float, ForeignKey, Enum, Boolean, text
from enum import Enum as PyEnum


class UserRole(PyEnum):
    ADMIN = "ADMIN"
    USER = "USER"


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    use_lang = Column(String(50), nullable=False, server_default="python3")  # 사용언어
    username = Column(String(255), nullable=False)
    nickname = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    role = Column(Enum(UserRole), nullable=False, server_default="USER")
    profile_img_url = Column(Text, nullable=True)  # 프로필 이미지 주소


class UserMmr(Base):
    __tablename__ = "user_mmr"
    mmr_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    rating = Column(Float, nullable=False, server_default="1000")
    rating_devi = Column(Float, nullable=False, server_default="350")
    volatility = Column(Float, nullable=False, server_default="0.06")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MatchResult(str, PyEnum):
    WIN = "win"
    DRAW = "draw"
    LOSS = "loss"


class MatchLog(Base):
    __tablename__ = "match_log"
    match_log_id = Column(Integer, primary_key=True, autoincrement=True)
    # match_id = Column(Integer, ForeignKey("matches.match_id"))
    user_id = Column(Integer, ForeignKey("users.user_id"))
    # problem_id = Problem 테이블 완성 시 설정
    result = Column(Enum(MatchResult))
    mmr_earned = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_consumed = Column(Boolean, server_default=text("FALSE"))
