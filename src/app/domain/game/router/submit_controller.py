from fastapi import APIRouter
from sse_starlette.sse import EventSourceResponse
from src.app.domain.game.schemas import game_schemas as schemas
from src.app.domain.game.service import game_service as service

router = APIRouter()


@router.post("/submit")
async def submit_code(request: schemas.SubmitRequest):
    event_generator = service.stream_evaluate_code(request.language, request.code, request.problem_id)
    return EventSourceResponse(event_generator)
