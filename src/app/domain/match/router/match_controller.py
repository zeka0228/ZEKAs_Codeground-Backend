from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.app.utils.ws_manager import WSManager
import asyncio

router = APIRouter()
ws_manager = WSManager()
match_id_counter = 1


@router.websocket("/ws/match/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: int):
    user_id = int(user_id)
    await ws_manager.connect(user_id, websocket)
    ws_manager.add_to_queue(user_id)

    try:
        """
        이 안 어딘가에 매칭 알고리즘 기반으로 user1, 2를 선택하는 기능을 추가하라 @초갈 듀오
        """
        # 매칭 대기 후 상대 유저와 매칭 시도
        await try_matching()

        while True:
            data = await websocket.receive_json()
            if data["type"] == "match_accept":
                await handle_accept(data["match_id"], user_id)
            elif data["type"] == "match_reject":
                await handle_match_reject(data["match_id"], user_id)
            elif data["type"] == "cancel_queue":
                ws_manager.remove_from_queue(user_id)
                await websocket.send_json({"type": "queue_cancelled"})

    except WebSocketDisconnect:
        ws_manager.disconnect(user_id)
    finally:
        ws_manager.remove_from_queue(user_id)


async def try_matching():
    global match_id_counter
    user1, user2 = ws_manager.pop_from_queue()
    if not user1 or not user2:
        return

    match_id = match_id_counter
    match_id_counter += 1

    ws_manager.match_state[match_id][user1] = False
    ws_manager.match_state[match_id][user2] = False

    # 선택된 유저 1, 2 에게 매칭이 되었으니 게임을 진행할 것인지 여부를 묻기 위한 메시지 전송
    await ws_manager.broadcast(
        [user1, user2], {"type": "match_found", "match_id": match_id, "opponent_ids": [user1, user2], "time_limit": 20}
    )

    # 타이머 처리 (20초 안에 둘 다 수락하지 않으면 매칭 취소)
    asyncio.create_task(handle_match_timeout(match_id, [user1, user2], 20))


async def handle_accept(match_id: int, user_id: int):
    if match_id not in ws_manager.match_state:
        return

    ws_manager.match_state[match_id][user_id] = True
    users = list(ws_manager.match_state[match_id].keys())

    if all(ws_manager.match_state[match_id].values()):
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
