from fastapi import APIRouter, Depends
from sse_starlette.sse import EventSourceResponse
from src.app.domain.game.schemas import game_schemas as schemas
from src.app.domain.game.service import game_service as service
from sqlalchemy.orm import Session
from src.app.core.database import get_db
from src.app.core.security import get_current_user
from src.app.models.models import User

router = APIRouter()


@router.post("/submit")
async def submit_code(request: schemas.SubmitRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    event_generator = service.stream_evaluate_code(db, current_user.user_id, request.match_id, request.language, request.code, request.problem_id)
    return EventSourceResponse(event_generator)
