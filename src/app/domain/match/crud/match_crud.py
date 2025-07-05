from src.app.models.models import MatchLog
from typing import Optional
from sqlalchemy.orm import Session
from src.app.models.models import Match, UserMmr


async def get_mmr_by_id(db: Session, user_id: int) -> Optional[UserMmr]:  # User -> Optional[User]로 수정
    return db.query(UserMmr).filter(UserMmr.user_id == user_id).first()


async def get_log_by_id(db: Session, input_id: int) -> Optional[MatchLog]:
    return db.query(MatchLog).filter(MatchLog.user_id == input_id, MatchLog.is_consumed.is_(False)).first()


async def get_log_by_game_id(db: Session, match_id: int, input_id: int) -> Optional[MatchLog]:
    return db.query(MatchLog).filter(MatchLog.user_id == input_id, MatchLog.match_id == match_id).first()


async def create_match(db: Session, problem_id: int):
    match = Match(problem_id=problem_id, matching_status="created")
    db.add(match)
    db.flush()
    db.refresh(match)
    return match


async def create_match_logs(db: Session, match_id: int, user_ids: list[int], problem_id: int):
    user_a_mmr = await get_mmr_by_id(db, user_ids[0])
    user_b_mmr = await get_mmr_by_id(db, user_ids[1])

    user_a_log = MatchLog(
        match_id=match_id,
        problem_id=problem_id,
        user_id=user_ids[0],
        is_consumed=False,
        opponent_mmr=user_b_mmr.rating,
        opponent_rd=user_b_mmr.rating_devi,
    )

    user_b_log = MatchLog(
        match_id=match_id,
        problem_id=problem_id,
        user_id=user_ids[1],
        is_consumed=False,
        opponent_mmr=user_a_mmr.rating,
        opponent_rd=user_a_mmr.rating_devi,
    )

    db.add_all([user_a_log, user_b_log])
    db.commit()
    return


async def get_match_logs_by_user_id(db: Session, user_id: int):
    return db.query(MatchLog).filter(MatchLog.user_id == user_id).order_by(MatchLog.created_at.desc()).all()
