from src.app.domain.match.utils.queues import hard_queue, normal_queue, queue_lock
from src.app.domain.match.utils.matcher import hybrid_match, hard_match, force_match
from datetime import datetime, timezone
import asyncio
from sqlalchemy.orm import Session
from src.app.domain.match.crud import match_crud
from src.app.domain.problem.crud import problem_crud
from src.app.models.models import Match
from src.app.utils.ws_manager import ws_manager

from itertools import count

# 매칭 루프 타이머
MATCH_INTERVAL = 1  # 초 세팅 0.5 = 500ms
GO_TO_HARD = 180  # 강제 풀 배치 기준 180 = 180s
match_id_counter = count(1)


class MatchService:
    def __init__(self):
        self._interval = MATCH_INTERVAL
        self._task: asyncio.Task | None = None

    async def _run(self):
        while True:
            await asyncio.sleep(self._interval)
            await self._tick()

    @staticmethod
    async def _tick():
        async with queue_lock:
            users = list(normal_queue) + list(hard_queue)
            if len(users) < 2:
                return

            (pairs, pre_waiting), algo = hybrid_match(users)

            normal_queue.clear()
            hard_queue.clear()

            hard_list = []
            waiting = []
            now = datetime.now(timezone.utc)
            for user in pre_waiting:
                if (now - user.joined_at).total_seconds() >= GO_TO_HARD:
                    hard_list.append(user)
                else:
                    waiting.append(user)

            # 강제 풀 매칭
            if len(hard_list) > 0:
                # 강제 그리디 1차 (hard 끼리)
                if len(hard_list) > 1:
                    hard_pairs, hard_waiter = hard_match(hard_list)
                    pairs.extend(hard_pairs)
                    hard_list = []
                    if hard_waiter:
                        hard_list.append(hard_waiter)

                # 강제 그리디 2차 (그냥 가까운 놈 납치)
                if len(hard_list) == 1:
                    if len(waiting) > 0:
                        victim = force_match(hard_list[0], waiting)
                        pairs.append((hard_list[0], victim))
                        waiting.remove(victim)
                    else:
                        hard_queue.append(hard_list[0])
            normal_queue.extend(waiting)
        # 매칭 성공 쌍에게 매칭 완료 함수 시행
        await dispatch_pairs(pairs, algo)

    def start(self):

        if self._task is None:
            self._task = asyncio.create_task(self._run())

    async def stop(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


async def dispatch_pairs(pairs, algo):
    """
    pairs: List[Tuple[MatchingUserInfo, MatchingUserInfo]]
    """

    for u1, u2 in pairs:
        match_id = next(match_id_counter)

        ws_manager.match_state[match_id] = {
            u1.id: False,
            u2.id: False,
        }

        await ws_manager.broadcast(
            [u1.id, u2.id],
            {
                "type": "match_found",
                "match_id": match_id,
                "opponent_ids": [u1.id, u2.id],
                "time_limit": 20,
                "algo": algo,
            },
        )

        # 20초 타임아웃
        asyncio.create_task(handle_match_timeout(match_id, [u1.id, u2.id], 20))


async def handle_match_timeout(match_id: int, users: list[int], timeout: int):
    await asyncio.sleep(timeout)
    if match_id in ws_manager.match_state and not all(ws_manager.match_state[match_id].values()):
        await ws_manager.broadcast(users, {"type": "match_cancelled", "reason": "timeout or rejection"})
        ws_manager.match_state.pop(match_id, None)


async def create_match_with_logs(db: Session, user_ids: list[int]) -> tuple[Match, int]:
    problem = await problem_crud.get_random_problem(db)
    match = await match_crud.create_match(db, problem.problem_id)
    await match_crud.create_match_logs(db, match.match_id, user_ids, problem.problem_id)
    db.commit()
    return match, problem.problem_id


match_service = MatchService()
