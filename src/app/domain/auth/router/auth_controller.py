from typing import Annotated

from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.app.core.database import get_db
from src.app.domain.auth.schemas import auth_schemas as schemas
from src.app.domain.auth.service import auth_service as service
from src.app.core.security import create_access_token
from src.app.domain.auth.crud import auth_crud as crud
from fastapi import APIRouter, Depends, HTTPException, status, Response

router = APIRouter()

DB = Annotated[Session, Depends(get_db)]


@router.post("/sign-up")
async def sign_up(response: Response, sign_up_request: schemas.UserSignupRequest, db: DB):
    try:
        # 1. 이메일이 있는지(중복 가입) 확인한다.
        await service.check_duplicate_email(db, str(sign_up_request.email))
        # 2. 닉네임이 있는지(중복 여부) 확인한다.
        await service.check_duplicate_nickname(db, sign_up_request.nickname)  # ← 추가
        # 3. 회원가입 진행
        await service.join(db, sign_up_request)
        db.commit()
        # 3. 회원가입 성공 시 새로운 acces_token 생성
        access_token = create_access_token(subject=sign_up_request.email)
        # 4. 반환
        return schemas.TokenResponse(access_token=access_token)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        print("회원가입 에러:", repr(e))  # 에러 내용 자세히 출력
        raise HTTPException(status_code=500, detail="서버 오류로 회원가입에 실패했습니다.")


@router.post("/login")
async def login(
    db: DB,
    from_data: OAuth2PasswordRequestForm = Depends(),
):
    try:
        user = await service.authenticate_user(db, from_data.username, from_data.password)

        access_token = create_access_token(subject=user.email)
        return schemas.TokenResponse(access_token=access_token)
    except HTTPException as e:
        raise e
    except Exception as e:
        print(e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")  # 쿠키 사용 시
    return {"message": "로그아웃 되었습니다."}


@router.get("/find-id")
async def find_id(email: str, db: DB):
    user = await crud.get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="등록되지 않은 이메일입니다.")
    return {"username": user.username, "nickname": user.nickname}


@router.get("/check-email")
async def check_email(email: str, db: DB):
    if await service.check_email_exists(db, email):
        raise HTTPException(status_code=400, detail="이미 사용 중인 이메일입니다.")
    return {"available": True}


@router.get("/check-nickname")
async def check_nickname(nickname: str, db: DB):
    if await service.check_nickname_exists(db, nickname):
        raise HTTPException(status_code=400, detail="이미 사용 중인 닉네임입니다.")
    return {"available": True}


@router.post("/reset-password/request")
async def request_password_reset(email: str, db: DB):
    await service.send_reset_password_email(db, email)
    return {"message": "비밀번호 초기화 메일을 발송했습니다."}


@router.post("/reset-password/verify")
async def verify_reset_code(email: str, code: str, db: DB):
    await service.verify_reset_code(db, email, code)
    return {"message": "인증 성공"}


@router.post("/reset-password/complete")
async def complete_password_reset(email: str, code: str, new_password: str, db: DB):
    await service.reset_password(db, email, code, new_password)
    return {"message": "비밀번호가 성공적으로 변경되었습니다."}
