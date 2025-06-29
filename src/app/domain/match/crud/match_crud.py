from src.app.models.models import MatchLog, MatchResult
from typing import Optional
from src.app.domain.match.utils.mmr_measure import full_update, MatchScore
from src.app.domain.user.crud.user_crud import get_user_by_id
from sqlalchemy.orm import Session
from src.app.models.models import UserMmr


async def get_mmr_by_id(db: Session, user_id: int) -> Optional[UserMmr]:  # User -> Optional[User]로 수정
    return db.query(UserMmr).filter(UserMmr.user_id == user_id).first()


async def get_log_by_id(db: Session, input_id: int) -> Optional[MatchLog]:
    return db.query(MatchLog).filter(MatchLog.user_id == input_id, MatchLog.is_consumed.is_(False)).first()

RESULT_TO_SCORE = {
    MatchResult.WIN:  MatchScore.WIN,
    MatchResult.DRAW: MatchScore.DRAW,
    MatchResult.LOSS: MatchScore.LOSS,
}

async def update_users_mmr(db: Session, user_id: int) -> None:
    user_info = await get_user_by_id(db, user_id)
    user_mmr_info = await get_mmr_by_id(db, user_id)
    match_log = await get_log_by_id(db, user_id)

    if None in (user_info, user_mmr_info, match_log):
        return


    ori_mmr = user_info.my_tier

    enemy_mmr = match_log.opponent_mmr
    enemy_rd = match_log.opponent_rd
    score_enum = RESULT_TO_SCORE[match_log.result]  # ← Enum 변환
    game = [(enemy_mmr, enemy_rd, score_enum)]

    new_rate, new_rd, new_sigma = full_update(user_info.my_tier, user_mmr_info.rating_devi, user_mmr_info.volatility, game)

    user_info.my_tier = new_rate
    user_mmr_info.rating_devi = int(new_rd)
    user_mmr_info.volatility = new_sigma

    match_log.mmr_earned = new_rate - ori_mmr
    match_log.is_consumed = True

    db.commit()

    return

async def create_log(db: Session, match_id : int, user_a_id: int, user_b_id : int, winner : int | None) -> None:
    user_a = await get_user_by_id(db, user_a_id)
    user_b = await get_user_by_id(db, user_b_id)
    user_a_mmr = await get_mmr_by_id(db, user_a_id)
    user_b_mmr = await get_mmr_by_id(db, user_b_id)

    user_a_log = MatchLog(
        user_id=user_a_id,
        match_id=match_id,
        mmr_earned= 0,
        opponent_mmr = user_b.my_tier,
        opponent_rd = user_b_mmr.rating_devi
    )

    user_b_log = MatchLog(
        user_id=user_b_id,
        match_id=match_id,
        mmr_earned=0,
        opponent_mmr=user_a.my_tier,
        opponent_rd=user_a_mmr.rating_devi
    )

    if not winner:
        user_a_log.result = MatchResult.DRAW
        user_b_log.result = MatchResult.DRAW
    else:
        if winner == user_a.user_id:
            user_a_log.result = MatchResult.WIN
            user_b_log.result = MatchResult.LOSS
        else:
            user_a_log.result = MatchResult.LOSS
            user_b_log.result = MatchResult.WIN

    db.add_all([user_a_log, user_b_log])
    db.commit()
    return
