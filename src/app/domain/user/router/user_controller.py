from typing import Annotated

from sqlalchemy.orm import Session

from src.app.core.database import get_db
from src.app.core.security import get_current_user
from src.app.domain.user.schemas import user_schemas as schemas
from src.app.domain.user.service import user_service as service
from src.app.models.models import User

from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter()

DB = Annotated[Session, Depends(get_db)]
VALID_USER = Annotated[User, Depends(get_current_user)]


@router.get("/me", response_model=schemas.UserResponseDto)
async def get_user_me(
    db: DB,
    current_user: VALID_USER,
) -> schemas.UserResponseDto:
    try:
        user = await service.get_user_data(db, current_user.user_id)
        return schemas.UserResponseDto.model_validate(user)
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
