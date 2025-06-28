import asyncio
from collections import deque
from sqlalchemy.orm import Session
from src.app.models.models import User
from src.app.domain.match.crud import match_crud as crud
from src.app.domain.match.utils.mmr_measure import inflate_rd
from src.app.domain.match.schemas.match_schemas import MatchingUserInfo
from datetime import datetime, timezone

normal_queue: deque = deque()
hard_queue: deque = deque()
queue_lock: asyncio.Lock = asyncio.Lock()


async def enqueue_user(db: Session, user: User) -> None:
    user_mmr = await crud.get_mmr_by_id(db, user.user_id)
    # 변동 rd 값 저장, db에 반영은 x(겜 끝났을 때만)
    rd = inflate_rd(user_mmr.rating_devi, user_mmr.volatility, user_mmr.updated_at)
    waiting_user = MatchingUserInfo(id=user.user_id, mmr=user.my_tier, rd=rd, joined_at=datetime.now(timezone.utc))

    async with queue_lock:
        # 이미 큐에 있는지 검사
        if _exists_in_queue(waiting_user["user_id"]):
            return  # 혹은 raise HTTPException(400, "already joined")

        normal_queue.append(waiting_user)


async def dequeue_user(user_id: int) -> None:
    for q in (normal_queue, hard_queue):
        for i, u in enumerate(q):
            if u["user_id"] == user_id:
                del q[i]
                break
    return


def _exists_in_queue(user_id: int) -> bool:
    return any(u["user_id"] == user_id for u in normal_queue) or any(u["user_id"] == user_id for u in hard_queue)
