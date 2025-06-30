from src.app.models.models import MatchLog
from typing import Optional
from sqlalchemy.orm import Session
from src.app.models.models import Match, UserMmr


async def get_mmr_by_id(db: Session, user_id: int) -> Optional[UserMmr]:  # User -> Optional[User]로 수정
    return db.query(UserMmr).filter(UserMmr.user_id == user_id).first()


async def get_log_by_id(db: Session, input_id: int) -> Optional[MatchLog]:
    return db.query(MatchLog).filter(MatchLog.user_id == input_id, MatchLog.is_consumed.is_(False)).first()


async def create_match(db: Session, problem_id: int):
    match = Match(problem_id=problem_id, matching_status="created")
    db.add(match)
    db.flush()
    db.refresh(match)
    return match


async def create_match_logs(db: Session, match_id: int, user_ids: list[int], problem_id: int):
    for uid in user_ids:
        db.add(
            MatchLog(
                match_id=match_id,
                user_id=uid,
                problem_id=problem_id,
            )
        )
