from typing import Optional
from sqlalchemy.orm import Session
from src.app.models.models import UserMmr


async def get_mmr_by_id(db: Session, user_id: int) -> Optional[UserMmr]:  # User -> Optional[User]로 수정
    return db.query(UserMmr).filter(UserMmr.user_id == user_id).first()
