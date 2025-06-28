from sqlalchemy.orm import Session
from src.app.models.models import User
from src.app.domain.auth.schemas import auth_schemas as schemas
from typing import Optional  # 추가 코드


async def get_user_by_email(db: Session, email: str) -> Optional[User]:  # User -> Optional[User]로 수정
    return db.query(User).filter(User.email == email).first()


async def get_by_email(db: Session, email: str) -> bool:
    search_email = db.query(User).filter(User.email == email).first()
    return True if search_email else False


async def get_by_nickname(db: Session, nickname: str) -> bool:
    return db.query(User).filter(User.nickname == nickname).first() is not None


async def join_user(db: Session, sign_up_request: schemas.UserSignupRequest) -> User:
    new_user = User(
        username=sign_up_request.username,
        email=str(sign_up_request.email),
        nickname=sign_up_request.nickname,
        password=sign_up_request.password,  # 해시된 값
        use_lang=sign_up_request.use_lang,  # 사용언어 선택
    )
    db.add(new_user)
    return new_user
