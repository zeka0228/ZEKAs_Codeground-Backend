from typing import Tuple
from fastapi import APIRouter, HTTPException, WebSocket, Query
from starlette.websockets import WebSocketDisconnect
import asyncio
from src.app.domain.custom_room.crud import custom_room_crud as crud
from src.app.domain.custom_room.schemas.custom_room_schema import UserState, CustomRoom, RoomCreateRequest
from src.app.utils.logging import logger
import json
from src.app.utils.game_session import custom_game_rooms
router = APIRouter()

RECONNECT_TIMEOUT = 5

@router.post("/create_room/{user_id}")
async def create_room(room : RoomCreateRequest, user_id : int):
    room_id = await crud.alloc_room_id()
    if room_id is None:
        raise HTTPException(status_code=409, detail="No empty slots available.")
    title = room.title
    category = room.category
    difficulty = room.difficulty
    lang = room.use_language
    maker = UserState(user_id = user_id, ready = True, screen_sharing = False, screen_sharing_ready= False, connected = False)
    new_room = CustomRoom(room_id = room_id,
                          title = title,
                          category=category,
                          use_language=lang,
                          difficulty=difficulty,
                          user= None,
                          maker=maker,
                          is_gaming=False)
    await crud.send_room_info(new_room)
    return {"room_id": room_id, "result": "ok"}


@router.put("/join_room/{room_id}/{user_id}", response_model=CustomRoom)
async def join_room(room_id : int, user_id : int):
    return await crud.join_to_room(room_id, user_id)

@router.put("/leave_room/{room_id}/{user_id}")
async def leave_room(room_id : int, user_id : int):
    await crud.leave_from_room(room_id, user_id)
    return {"result": "ok"}


@router.websocket("/ws/room/{room_id}")
async def room_websocket(websocket: WebSocket, room_id: int, user_id: int = Query(...)):
    room = await crud.get_room_info(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    user_id = int(user_id)
    try:
        await websocket.accept()
    except RuntimeError as e:
        print(f"[WebSocket] accept() 실패: {e}")
        return


    await crud.connect_user(room.room_id, user_id)

    # 인증 : 해당 사설방 정보에 적혀있는 유저인지 확인
    if user_id != room.maker.user_id and user_id != room.user.user_id:
        logger.warning(f"Unauthorized connection attempt by user {user_id} to custom_match {room_id}")
        await websocket.accept()  # 반드시 먼저 accept
        await websocket.close(code=4001)
        return

# 재연결 감지 및 알림
    if (room.user.user_id == user_id and room.user.connected is False) or (room.maker.user_id == user_id and room.maker.connected is False):
        await crud.connect_user(room.room_id, user_id)
        logger.info(f"User {user_id} reconnected to custom_match {room_id}")
        await crud.publish_to_custom_room(
            room_id,
            {
                "type": "opponent_rejoined",
                "user_id": user_id,
                "room_id": room_id,
                "message": "상대방이 다시 연결되었습니다.",
            }
        )
    custom_game_rooms[room.room_id].append(websocket)

    try:
        while True:
            message = await websocket.receive_text()
            logger.debug(f"Received message from user {user_id} in custom match {room_id}: {message}")
            await handle_custom_match_message(websocket, room_id, user_id, message)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected from custom_match {room_id}")

        if websocket in custom_game_rooms[room.room_id]:
            custom_game_rooms[room.room_id].remove(websocket)

        await crud.disconnect_user(room.room_id, user_id)
        await crud.screen_share_stopped(room.room_id, user_id)

        async def delayed_leave():
            await asyncio.sleep(RECONNECT_TIMEOUT)
            # 아직 재접속되지 않았다면 ‘완전 이탈’ 처리
            (current_user, opponent) = await define_users(room.room_id, user_id)
            if not current_user.connected:
                logger.info(f"User {user_id} permanently left custom match {room.room_id}")
                # 상대방에게 이탈 알림
                await process_custom_result(room_id, opponent.user_id, "abandon")

                # 방 정리
                await crud.leave_from_room(room.room_id, user_id)
                await crud.end_game(room.room_id)

        asyncio.create_task(delayed_leave())

async def handle_custom_match_message(websocket : WebSocket, room_id : int, user_id : int , message : str):
    (current_user, opponent) = await define_users(room_id, user_id)
    try:
        data = json.loads(message)
        message_type = data.get("type")
        logger.info(f"Handling message type '{message_type}' for user {user_id} in game {room_id}")


        if message_type == "chat":
            # 채팅 메시지 전체 브로드캐스트
            await crud.publish_to_custom_room(room_id, {"type": "chat", "sender": user_id, "message": data.get("message")})

        elif message_type == "webrtc_signal":
            logger.debug(f"Broadcasting WebRTC signal from {user_id} in custom match {room_id}")
            # ICE candidate 혹은 SDP 교환
            await crud.publish_to_custom_room(room_id, {"type": "webrtc_signal", "sender": user_id, "signal": data.get("signal")})

        elif message_type == "ready":
            await crud.screen_share_ready(room_id, user_id)
            await crud.publish_to_custom_room(room_id, {"type": "player_ready", "user_id": user_id})
            logger.info(f"User {user_id} is ready in custom match {room_id}")
            if opponent.screen_sharing_ready:
                logger.info(f"All players are ready in custom match {room_id}")
                await crud.publish_to_custom_room(room_id, {"type": "all_ready"})

        elif message_type == "system_warning":
            await crud.publish_to_custom_room(room_id,{
                "type": "system_warning",
                "event": data.get("event"),
                "count": data.get("count"),
                "message": data.get("message"),
                "user_id": user_id,  # 누가 보낸 건지 구분용
            })

        elif message_type == "screen_share_stopped":
            await crud.screen_share_stopped(room_id, user_id)
            logger.info(f"Screen share stopped by user {user_id} in custom match {room_id}")
            # 상대방에게 화면 공유 중단 알림 전송
            await crud.publish_to_custom_room(room_id,{
                    "type": "screen_share_stopped",
                    "user_id": user_id,
                    "message": "화면 공유가 중지되었습니다.",
                })

        elif message_type == "screen_share_started":
            await crud.screen_share_started(room_id, user_id)
            logger.info(f"Screen share started by user {user_id} in custom match {room_id}")
            await crud.publish_to_custom_room(room_id,{
                    "type": "screen_share_started",
                    "user_id": user_id,
                    "message": "상대방이 화면 공유를 시작했습니다.",
                })
        elif message_type == "renegotiate_screen_share":
            await crud.publish_to_custom_room(room_id,{
                    "type": "renegotiate_screen_share",
                    "user_id": user_id,
                    "message": "상대방이 화면 공유 재협상을 요청했습니다.",
                })
        elif message_type == "match_result":
            reason = data.get("reason")
            if reason == "surrender":
                winner_id = opponent.user_id
            elif reason == "finish":
                winner_id = current_user.user_id
            else:
                winner_id = None
            await process_custom_result(room_id, winner_id, reason)

        else:
            logger.warning(f"Unknown message type received in custom match {room_id}: {message_type}")
            await websocket.send_json({"type": "error", "message": "Unknown message type"})

    except Exception as e:
        logger.error(f"Error handling message in custom match {room_id} : {e}")
        await websocket.send_json({"type": "error", "message": str(e)})


# 경기 결과 반환, 커스텀 매치라 점수 반영 X
# reason : surrender / abandon / finish / timeover
async def process_custom_result(room_id: int, winner_id: int | None, reason : str):
    await crud.publish_to_custom_room(
        room_id,
        {
            "type": "match_result",
            "room_id": room_id,
            "winner_id": winner_id,
            "reason": reason,
        }
    )



async def define_users(room_id : int, user_id : int)-> Tuple[UserState, UserState]:
    updated_room = await crud.get_room_info(room_id)
    if updated_room.maker.user_id == user_id:
        return updated_room.maker, updated_room.user
    else:
        return updated_room.user, updated_room.maker



