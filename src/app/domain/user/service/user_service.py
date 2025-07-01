from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.app.domain.user.crud import user_crud as crud
from src.app.domain.user.schemas import user_schemas as schemas
from src.app.core.password import get_password_hash, verify_password as verify_pw


async def get_user_data(db: Session, input_id: int) -> schemas.UserDto:
    user = crud.get_user_by_id(db, input_id=input_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return schemas.UserDto.model_validate(user)


async def update_my_profile(
    db: Session,
    user_id: int,
    nickname: str | None,
    current_password: str | None,
    new_password: str | None,
    profile_img_url: str | None = None,
):
    user = crud.get_user_by_id(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if new_password:
        if not current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="현재 비밀번호를 입력해야 합니다.",
            )
        if not verify_pw(current_password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="현재 비밀번호가 일치하지 않습니다.",
            )
        user.password = get_password_hash(new_password)

    if nickname:
        user.nickname = nickname

    if profile_img_url:
        user.profile_img_url = profile_img_url

    crud.update_user(db, user)
    return user
