from fastapi import APIRouter
from src.app.domain.game.schemas import game_schemas as schemas
from src.app.domain.game.service import game_service as service

router = APIRouter()

@router.post("/submit", response_model=schemas.SubmitResponse)
async def submit_code(request: schemas.SubmitRequest):
    result = await service.evaluate_code(request.language, request.code)
    return schemas.SubmitResponse(**result)
