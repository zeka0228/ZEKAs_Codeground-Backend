from fastapi import WebSocket, WebSocketDisconnect, APIRouter, Query
from src.app.utils.game_session import game_rooms, game_user_map, ready_status
import json

router = APIRouter()


@router.websocket("/ws/game/{game_id}")
async def game_websocket(websocket: WebSocket, game_id: int, user_id: int = Query(...)):
    game_id = int(game_id)
    user_id = int(user_id)

    # 인증: 해당 게임방에 참여할 자격이 있는지 확인
    if game_id not in game_user_map or user_id not in game_user_map[game_id]:
        await websocket.close(code=4001)
        return

    await websocket.accept()
    game_rooms[game_id].append(websocket)

    try:
        while True:
            # 클라이언트에서 받은 메시지를 처리 핸들러로 전달
            message = await websocket.receive_text()

            await handle_game_message(websocket, game_id, user_id, message)

    except WebSocketDisconnect:
        # 연결 종료 시 정리
        if websocket in game_rooms[game_id]:
            game_rooms[game_id].remove(websocket)

        if not game_rooms[game_id]:
            game_rooms.pop(game_id, None)

            # game_user_map.pop(game_id, None)
            ready_status.pop(game_id, None)


async def handle_game_message(websocket: WebSocket, game_id: int, user_id: int, message: str):
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

        elif message_type == "submit":
            # 채점 요청은 백엔드 채점 큐로 전달 (여기서는 예시용 로깅만)
            # 실제로는 RabbitMQ, Redis 등 MQ에 넣어야 함
            print(f"채점 요청: 사용자 {user_id}, 코드: {data.get('code')}")
            await websocket.send_json({"type": "submission_received"})

        elif message_type == "match_result":
            # 게임 종료: 결과 공유
            await broadcast_to_room(
                game_id, {"type": "match_result", "winner": data.get("winner"), "reason": data.get("reason")}
            )

        else:
            await websocket.send_json({"type": "error", "message": "Unknown message type"})

    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})


# 게임 내에서 발생하는 WebSocket 메시지를 처리하는 핵심 함수
async def broadcast_to_room(game_id: int, message: dict, exclude: WebSocket = None):
    for ws in game_rooms[game_id]:
        if ws != exclude:
            await ws.send_json(message)
