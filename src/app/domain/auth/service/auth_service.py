from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.app.domain.auth.crud import auth_crud as crud
from src.app.domain.auth.schemas import auth_schemas as schemas
from src.app.core.security import get_password_hash, verify_password


async def check_duplicate_email(db: Session, email: str) -> bool:
    query_email_result = await crud.get_by_email(db=db, email=email)
    if query_email_result:
        raise HTTPException(detail="Email already registered", status_code=status.HTTP_400_BAD_REQUEST)
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
