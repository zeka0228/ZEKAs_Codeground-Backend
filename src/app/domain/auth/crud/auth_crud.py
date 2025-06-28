from sqlalchemy.orm import Session
from src.app.models.models import User, UserMmr
from src.app.domain.auth.schemas import auth_schemas as schemas


async def get_user_by_email(db: Session, email: str) -> User:
    return db.query(User).filter(User.email == email).first()


async def get_by_email(db: Session, email: str) -> bool:
    search_email = db.query(User).filter(User.email == email).first()
    return True if search_email else False


async def join_user(db: Session, sign_up_request: schemas.UserSignupRequest) -> User:
    new_user = User(
        username=sign_up_request.username,
        email=sign_up_request.email,
        nickname=sign_up_request.nickname,
        password=sign_up_request.password,
    )
    db.add(new_user)
    # mmr db 반영 추가
    db.flush()
    mmr_row = UserMmr(user_id=new_user.user_id)
    db.add(mmr_row)
    return new_user
