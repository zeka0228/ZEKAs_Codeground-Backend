from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from src.app.domain.user.crud import user_crud as crud
from src.app.domain.user.schemas import user_schemas as schemas


async def get_user_data(db: Session, input_id: int) -> schemas.UserDto:
    user = await crud.get_user_by_id(db, input_id=input_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user
