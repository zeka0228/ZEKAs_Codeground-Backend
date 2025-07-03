from fastapi import Depends, WebSocket, WebSocketDisconnect, APIRouter, Query
from src.app.utils.game_session import game_rooms, game_user_map, ready_status
import json
from src.app.domain.game.service.game_result_service import update_user_log, update_match, search_result
from typing import Annotated
from sqlalchemy.orm import Session
from src.app.core.database import get_db

router = APIRouter()
DB = Annotated[Session, Depends(get_db)]


@router.websocket("/ws/game/{game_id}")
async def game_websocket(db: DB, websocket: WebSocket, game_id: int, user_id: int = Query(...)):
    game_id = int(game_id)
    user_id = int(user_id)

    # 인증: 해당 게임방에 참여할 자격이 있는지 확인
    if game_id not in game_user_map or user_id not in game_user_map[game_id]:
        await websocket.accept()  # 반드시 먼저 accept
        await websocket.close(code=4001)
        return

    await websocket.accept()
    game_rooms[game_id].append(websocket)
    ready_status[game_id][user_id] = False

    try:
        while True:
            # 클라이언트에서 받은 메시지를 처리 핸들러로 전달
            message = await websocket.receive_text()

            await handle_game_message(db, websocket, game_id, user_id, message)

    except WebSocketDisconnect:
        # 연결 종료 시 정리
        if websocket in game_rooms[game_id]:
            game_rooms[game_id].remove(websocket)

        if user_id in ready_status.get(game_id, {}):
            ready_status[game_id].pop(user_id, None)

            # Notify remaining players that this user disconnected
        if game_rooms.get(game_id):
            await broadcast_to_room(
                game_id,
                {
                    "type": "opponent_disconnected",
                    "user_id": user_id,
                },
            )

        if not game_rooms[game_id]:
            game_rooms.pop(game_id, None)

            # game_user_map.pop(game_id, None)
            ready_status.pop(game_id, None)


async def handle_game_message(db, websocket: WebSocket, game_id: int, user_id: int, message: str):
    opponent_id = [uid for uid in game_user_map[game_id] if uid != user_id][0]
    try:
        data = json.loads(message)
        message_type = data.get("type")

        if message_type == "chat":
            # 채팅 메시지 전체 브로드캐스트
            await broadcast_to_room(game_id, {"type": "chat", "sender": user_id, "message": data.get("message")})

        elif message_type == "webrtc_signal":
            # ICE candidate 혹은 SDP 교환
            await broadcast_to_room(
                game_id, {"type": "webrtc_signal", "sender": user_id, "signal": data.get("signal")}, exclude=websocket
            )

        elif message_type == "ready":
            ready_status[game_id][user_id] = True
            await broadcast_to_room(game_id, {"type": "player_ready", "user_id": user_id})
            if all(ready_status[game_id].values()):
                await broadcast_to_room(game_id, {"type": "all_ready"})

        elif message_type == "submit":
            # 채점 요청은 백엔드 채점 큐로 전달 (여기서는 예시용 로깅만)
            # 실제로는 RabbitMQ, Redis 등 MQ에 넣어야 함
            print(f"채점 요청: 사용자 {user_id}, 코드: {data.get('code')}")
            await websocket.send_json({"type": "submission_received"})

        # 제출 / 시간초과 / 항복 시 여기로
        # 각 reason 은 "finish" / "timeout" / "surrender"
        elif message_type == "match_result":
            reason = data.get("reason")
            print("시작")
            winner_id, reason = await process_match_result(db, game_id, user_id, opponent_id, reason)
            print(winner_id, reason)
            await websocket.send_json({"type": "match_result", "winner": winner_id, "reason": reason})

        else:
            print("에러 1")
            await websocket.send_json({"type": "error", "message": "Unknown message type"})

    except Exception as e:
        print("에러 2")
        await websocket.send_json({"type": "error", "message": str(e)})


# 게임 내에서 발생하는 WebSocket 메시지를 처리하는 핵심 함수
async def broadcast_to_room(game_id: int, message: dict, exclude: WebSocket = None):
    disconnected_sockets = []

    for ws in game_rooms.get(game_id, [])[:]:  # 복사본으로 안전 순회
        if ws == exclude:
            continue
        try:
            await ws.send_json(message)
        except WebSocketDisconnect:
            disconnected_sockets.append(ws)
        except Exception as e:
            print(f"[broadcast_to_room] 전송 중 예외 발생: {e}")
            disconnected_sockets.append(ws)

    for ws in disconnected_sockets:
        if ws in game_rooms[game_id]:
            game_rooms[game_id].remove(ws)

async def process_match_result(
    db: Session, game_id: int, user_id: int, opponent_id: int, reason: str
) -> (int | None, str):
    opponent_result = await search_result(db, game_id, opponent_id)
    # 기권 시
    if reason in ("surrender", "abandon"):
        await update_user_log(db, game_id, user_id, "loss")
        if opponent_result and opponent_result == "loss":
            await update_match(db, game_id, "abnormal")
        # 패배
        return opponent_id, "surrender"
    # 시간 초과 시
    elif reason == "timeout":
        # 상대방 상태 판단
        if opponent_result == "loss":
            await update_user_log(db, game_id, user_id, "win")
            await update_match(db, game_id, "abnormal")
            # 상대 기권 시 부전승
            return user_id, "walkover"

        elif opponent_result == "win":
            await update_user_log(db, game_id, user_id, "loss")
            # 상대가 이미 제출 완료 시 패배
            return opponent_id, "late"

        else:
            # 상대 또한 timeout 일 시, 무승부
            await update_user_log(db, game_id, user_id, "draw")
            await update_match(db, game_id, "draw")
            return None, "draw"

    else:
        if opponent_result == "win":
            await update_user_log(db, game_id, user_id, "loss")
            return opponent_id, "late"
        else:
            await update_user_log(db, game_id, user_id, "win")
            await update_match(db, game_id, "normal")
            return user_id, "finish"
