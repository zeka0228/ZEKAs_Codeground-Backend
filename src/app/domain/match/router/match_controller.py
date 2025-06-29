from typing import Annotated
from sqlalchemy.orm import Session

from src.app.core.database import get_db
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from src.app.utils.ws_manager import WSManager
from src.app.utils.game_session import game_user_map
import asyncio
from src.app.core.security import get_current_user
from src.app.models.models import User
from src.app.domain.match.utils.queues import enqueue_user, dequeue_user, queue_lock


router = APIRouter()
ws_manager = WSManager()
match_id_counter = 1

DB = Annotated[Session, Depends(get_db)]
VALID_USER = Annotated[User, Depends(get_current_user)]


@router.websocket("/ws/match/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int, db: DB, current_user: VALID_USER):
    user_id = int(user_id)

    # ── 2) 매칭 큐 등록 ────────────────────
    await enqueue_user(db, current_user)  # 반드시 await

    # ── 3) 웹소켓 등록 ─────────────────────
    await ws_manager.connect(user_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "match_accept":
                await handle_accept(data["match_id"], user_id)
            elif data["type"] == "match_reject":
                await handle_match_reject(data["match_id"], user_id)
            elif data["type"] == "cancel_queue":
                await match_cancel(user_id)  # ← 큐에서 제거
                await websocket.send_json({"type": "queue_cancelled"})
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
        await match_cancel(user_id)


# async def try_matching():
#     global match_id_counter
#     user1, user2 = ws_manager.pop_from_queue()
#     if not user1 or not user2:
#         return
#
#     match_id = match_id_counter
#     match_id_counter += 1
#
#     ws_manager.match_state[match_id][user1] = False
#     ws_manager.match_state[match_id][user2] = False
#
#     # 선택된 유저 1, 2 에게 매칭이 되었으니 게임을 진행할 것인지 여부를 묻기 위한 메시지 전송
#     await ws_manager.broadcast(
#         [user1, user2], {"type": "match_found", "match_id": match_id, "opponent_ids": [user1, user2], "time_limit": 20}
#     )
#
#     # 타이머 처리 (20초 안에 둘 다 수락하지 않으면 매칭 취소)
#     asyncio.create_task(handle_match_timeout(match_id, [user1, user2], 20))


async def handle_accept(match_id: int, user_id: int):
    if match_id not in ws_manager.match_state:
        return

    ws_manager.match_state[match_id][user_id] = True
    users = list(ws_manager.match_state[match_id].keys())

    if all(ws_manager.match_state[match_id].values()):
        users = list(ws_manager.match_state[match_id].keys())
        # 여기에서 게임방 유저 등록
        game_user_map[match_id + 1000] = users

        await ws_manager.broadcast(
            users, {"type": "match_accepted", "game_id": match_id + 1000, "join_url": f"/game/{match_id + 1000}"}
        )
        ws_manager.match_state.pop(match_id, None)


async def handle_match_timeout(match_id: int, users: list[int], timeout: int):
    await asyncio.sleep(timeout)
    if match_id in ws_manager.match_state and not all(ws_manager.match_state[match_id].values()):
        await ws_manager.broadcast(users, {"type": "match_cancelled", "reason": "timeout or rejection"})
        ws_manager.match_state.pop(match_id, None)


async def handle_match_reject(match_id: int, rejecting_user: int):
    if match_id not in ws_manager.match_state:
        return

    users = list(ws_manager.match_state[match_id].keys())

    await ws_manager.broadcast(users, {"type": "match_cancelled", "reason": "rejected", "rejected_by": rejecting_user})

    ws_manager.match_state.pop(match_id, None)


async def match_cancel(user_id: int):
    try:
        await asyncio.wait_for(queue_lock.acquire(), timeout=0)
    except asyncio.TimeoutError:
        # 매칭 루프가 돌면서 락을 잡고 있는 상태 → 요청만 무시
        return {"ok": True}

    try:
        await dequeue_user(user_id)

    finally:
        queue_lock.release()
    return {"ok": True}
