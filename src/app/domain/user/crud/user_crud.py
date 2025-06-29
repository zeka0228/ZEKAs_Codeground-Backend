from sqlalchemy.orm import Session
from src.app.models.models import User
from typing import  Optional

async def get_user_by_id(db: Session, input_id: int) -> Optional[User]:
    return db.query(User).filter(User.user_id == input_id).first()
