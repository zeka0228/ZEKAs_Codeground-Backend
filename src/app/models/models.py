from src.app.core.database import Base
from src.app.domain.match.utils.mmr_measure import RD_MAX, SIGMA_DEF
from sqlalchemy import Column, DateTime, Integer, String, func, Text, Float, ForeignKey, Enum, Boolean
from enum import Enum as PyEnum

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
    role = Column(String(50), nullable=False, server_default="user")  # 회원권한
    my_tier = Column(Float, nullable=False, server_default="1000")  # 내 티어
    profile_img_url = Column(Text, nullable=True)  # 프로필 이미지 주소

class UserMmr(Base):
    __tablename__ = "user_mmr"
    __table_args__ = {"schema": "mmr"}  # 스키마 분리
    mmr_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("public.users.user_id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    rating_devi = Column(Integer, nullable=False, server_default=str(RD_MAX))
    volatility = Column(Float, nullable=False, server_default=str(SIGMA_DEF))


class MatchResult(PyEnum):
    WIN  = "win"
    DRAW = "draw"
    LOSS = "loss"


class MatchLog(Base):
    __tablename__ = "match_log"
    __table_args__ = {"schema": "match_log"}
    match_log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("public.users.user_id", ondelete="CASCADE"), index=True)
    match_id = Column(Integer, ForeignKey("public.matches.match_id", ondelete="CASCADE"))
    #problem_id = Problem 테이블 완성 시 설정
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    result = Column(Enum(MatchResult, name="match_result"), nullable=False)
    mmr_earned = Column(Float, nullable=False, server_default="0" ) # 경기 종료 -> log 기록 -> 유저 mmr 업데이트하면서 동시에 업데이트
    opponent_mmr = Column(Float, nullable=False)
    opponent_rd = Column(Float, nullable=False)
    is_consumed = Column(Boolean, nullable=False, server_default="False",index=True)

