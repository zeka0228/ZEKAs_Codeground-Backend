import secrets
import datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.app.domain.auth.crud import auth_crud as crud
from src.app.domain.auth.schemas import auth_schemas as schemas
from src.app.core.security import get_password_hash, verify_password
from src.app.models.models import User
from src.app.utils.email import send_email  # 너희 메일 전송 유틸

reset_code_store = {}


async def check_duplicate_email(db: Session, email: str) -> bool:
    query_email_result = await crud.get_by_email(db=db, email=email)
    if query_email_result:
        raise HTTPException(detail="이미 사용 중인 이메일 입니다.", status_code=status.HTTP_400_BAD_REQUEST)
    return False


async def check_duplicate_nickname(db: Session, nickname: str) -> bool:
    user = db.query(User).filter(User.nickname == nickname).first()
    if user:
        raise HTTPException(detail="이미 사용 중인 닉네임 입니다.", status_code=status.HTTP_400_BAD_REQUEST)
    return False


async def join(db: Session, sign_up_request: schemas.UserSignupRequest) -> schemas.UserSignupResponse:
    # 1. 비밀 번호 해시
    hashed_password = get_password_hash(sign_up_request.password)
    sign_up_request.password = hashed_password
    # 2. crud 로직에 회원 저장 로직을 호출한다.
    join_user = await crud.join_user(db=db, sign_up_request=sign_up_request)
    if not join_user:
        raise HTTPException(detail="Fail Sign Up User", status_code=status.HTTP_400_BAD_REQUEST)
        # 3. 저장에 성공하면 True 실패하면 False를 반환받는다.
    return schemas.UserSignupResponse.model_validate(join_user)


async def authenticate_user(db: Session, email: str, password: str) -> schemas.UserDto:
    # 1. 유저 정보 조회
    user = await crud.get_user_by_email(db=db, email=email)
    if not user:
        raise HTTPException(detail="Invalid User Data", status_code=status.HTTP_401_UNAUTHORIZED)
    if not await verify_password(password, user.password):
        raise HTTPException(detail="Invalid Password", status_code=status.HTTP_401_UNAUTHORIZED)
    return schemas.UserDto.model_validate(user)


# 이메일 존재 여부 확인
async def check_email_exists(db: Session, email: str) -> bool:
    return await crud.get_by_email(db, email)


# 닉네임 존재 여부 확인
async def check_nickname_exists(db: Session, nickname: str) -> bool:
    return await crud.get_by_nickname(db, nickname)


async def send_reset_password_email(db: Session, email: str):
    user = await crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="등록되지 않은 이메일입니다.")
    code = secrets.token_hex(3)  # 예: "a1b2c3"
    expires = datetime.datetime.utcnow() + datetime.timedelta(minutes=10)
    reset_code_store[email] = (code, expires)
    await send_email(to=email, subject="비밀번호 초기화", body=f"인증코드: {code}")


async def verify_reset_code(db: Session, email: str, code: str):
    stored = reset_code_store.get(email)
    if not stored:
        raise HTTPException(status_code=400, detail="인증 요청이 없습니다.")
    if stored[0] != code:
        raise HTTPException(status_code=400, detail="잘못된 인증 코드입니다.")
    if stored[1] < datetime.datetime.utcnow():
        raise HTTPException(status_code=400, detail="인증 코드가 만료되었습니다.")


async def reset_password(db: Session, email: str, code: str, new_password: str):
    await verify_reset_code(db, email, code)
    user = await crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="유저 없음")
    user.password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    reset_code_store.pop(email, None)  # 인증 코드 제거
