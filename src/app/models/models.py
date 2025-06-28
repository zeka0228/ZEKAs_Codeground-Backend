from src.app.domain.match.utils.mmr_measure import RD_MAX, SIGMA_DEF
from sqlalchemy import Column, DateTime, Integer, String, func, Text, Float, ForeignKey
from src.app.core.database import Base


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


# mmr.user_mmr  ← MMR 전용 스키마
class UserMmr(Base):
    __tablename__ = "user_mmr"
    __table_args__ = {"schema": "mmr"}  # 스키마 분리
    mmr_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("public.users.user_id", ondelete="CASCADE"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    rating_devi = Column(Integer, nullable=False, server_default=str(RD_MAX))
    volatility = Column(Float, nullable=False, server_default=str(SIGMA_DEF))
