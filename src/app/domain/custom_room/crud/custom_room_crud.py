import json
import redis.asyncio as aioredis
from fastapi import HTTPException
from starlette.websockets import WebSocket
from src.app.utils.game_session import custom_game_rooms
from src.app.config.config import Settings
from src.app.domain.custom_room.schemas.custom_room_schema import CustomRoom, UserState
from dataclasses import asdict
import asyncio

rds = aioredis.Redis(host=Settings.REDIS_HOST, port=Settings.REDIS_PORT)
MAX_SLOT = 1000000 #1,000,000

async def alloc_room_id() -> int | None:
    for slot in range(MAX_SLOT):
        if await rds.getbit("room_slots", slot) == 0:
            await rds.setbit("room_slots", slot, 1)
            return slot
    return None # 빈방 없음

async def send_room_info(room: CustomRoom) -> None:
    room_dict = asdict(room)
    room_json = json.dumps(room_dict)
    await rds.set(f"room:{room.room_id}", room_json)
    await rds.rpush("room_list", room.room_id)
    asyncio.create_task(pubsub_listener(room.room_id))

async def get_room_info(room_id: int) -> CustomRoom | None:
    data = await rds.get(f"room:{room_id}")
    if data is None:
        return None
    room_dict = json.loads(data)
    return dict_to_custom_room(room_dict)

async def join_to_room(room_id: int, user_id : int) -> CustomRoom:
    data = await rds.get(f"room:{room_id}")
    if data is None:
        raise HTTPException(status_code=404, detail="No room found.")

    room_dict = json.loads(data)
    if room_dict.get("user") is not None:
        raise HTTPException(status_code=403, detail="Room already full.")

    user = UserState(user_id=user_id, ready=False, screen_sharing=False, connected=False)
    room_dict["user"] = asdict(user)
    await rds.set(f"room:{room_id}", json.dumps(room_dict))

    return dict_to_custom_room(room_dict)

async def leave_from_room(room_id: int, user_id: int) -> None:
    data = await rds.get(f"room:{room_id}")
    if data is None:
        raise HTTPException(status_code=404, detail="No room found.")
    room_dict = json.loads(data)
    maker_dict = room_dict.get("maker")
    if maker_dict.get("user_id") == user_id:
        remain_user_dict = room_dict.get("user")
        if remain_user_dict is None:
            await delete_room(room_id)

        else:
            remain_user_dict["ready"] = True
            room_dict["maker"] = remain_user_dict
            room_dict["user"] = None
            await rds.set(f"room:{room_id}", json.dumps(room_dict))
    else:
        room_dict["user"] = None
        await rds.set(f"room:{room_id}", json.dumps(room_dict))

    return

async def delete_room(room_id: int) -> None:
    pubsub = rds.pubsub()
    await pubsub.unsubscribe(f"room:{room_id}")
    await rds.setbit("room_slots", room_id, 0)
    await rds.lrem("room_list", 0, str(room_id))
    await rds.delete(f"room:{room_id}")
    return


async def get_rooms_by_list(page: int) -> list[CustomRoom]:
    page_size = 20
    start = page * page_size
    end = start + page_size - 1

    room_ids = await rds.lrange("room_list", start, end)
    rooms = []
    for room_id in room_ids:
        data = await rds.get(f"room:{int(room_id)}")
        if data:
            rooms.append(dict_to_custom_room(json.loads(data)))
    return rooms

async def start_game(room_id: int) -> None:
    data = await rds.get(f"room:{room_id}")
    if data is None:
        raise HTTPException(status_code=404, detail="No room found.")

    room_dict = json.loads(data)
    room_dict["is_gaming"] = True
    await rds.set(f"room:{room_id}", json.dumps(room_dict))
    return


async def end_game(room_id: int) -> None:
    data = await rds.get(f"room:{room_id}")
    if data is None:
        raise HTTPException(status_code=404, detail="No room found.")

    room_dict = json.loads(data)
    room_dict["is_gaming"] = False
    await rds.set(f"room:{room_id}", json.dumps(room_dict))
    return


async def ready_user(room_id: int, user_id : int):
    room = await get_room_info(room_id)
    if not room.user or room.user.user_id != user_id:
        raise HTTPException(status_code=403, detail="User not found.")

    room.user.ready = True
    room_dict = asdict(room)
    await rds.set(f"room:{room.room_id}", json.dumps(room_dict))
    return

async def unready_user(room_id: int, user_id: int):
    room = await get_room_info(room_id)
    if room.is_gaming:
        raise HTTPException(status_code=403, detail="Game already started.")
    if not room.user or room.user.user_id != user_id:
        raise HTTPException(status_code=403, detail="User not found.")

    room.user.ready = False
    room_dict = asdict(room)
    await rds.set(f"room:{room.room_id}", json.dumps(room_dict))
    return

async def disconnect_user(room_id: int, user_id: int):
    return await change_connected(room_id, user_id, False)

async def connect_user(room_id: int, user_id: int):
    return await change_connected(room_id, user_id, True)

async def screen_share_stopped(room_id: int, user_id: int):
    return await change_connected(room_id, user_id, False)

async def screen_share_started(room_id: int, user_id: int):
    return await change_connected(room_id, user_id, True)

async def screen_share_ready(room_id: int, user_id: int):
    room = await get_room_info(room_id)
    if room is None:
        raise HTTPException(status_code=404, detail="Room not found")
    user = room.user if room.user.user_id == user_id else room.maker
    user.screen_sharing_ready = True
    room_dict = asdict(room)
    await rds.set(f"room:{room.room_id}", json.dumps(room_dict))


def dict_to_custom_room(room_dict: dict) -> CustomRoom:
    maker = UserState(**room_dict["maker"]) if room_dict.get("maker") else None
    user = UserState(**room_dict["user"]) if room_dict.get("user") else None
    return CustomRoom(
        room_id=room_dict["room_id"],
        maker=maker,
        user=user,
        difficulty=room_dict["difficulty"],
        category=room_dict["category"],
        use_language=room_dict["use_language"],
        title=room_dict["title"],
        is_gaming=room_dict["is_gaming"],
    )


async def change_connected(room_id: int, user_id: int, connected: bool):
    room = await get_room_info(room_id)

    if user_id == room.user.user_id:
        room.user.connected = connected
    elif user_id == room.maker.user_id:
        room.maker.connected = connected
    else:
        raise HTTPException(status_code=403, detail="User not found.")

    room_dict = asdict(room)
    await rds.set(f"room:{room.room_id}", json.dumps(room_dict))
    return

async def change_screen_share(room_id: int, user_id: int, sharing: bool):
    room = await get_room_info(room_id)

    if user_id == room.user.user_id:
        room.user.screen_sharing = sharing
    elif user_id == room.maker.user_id:
        room.maker.screen_sharing = sharing
    else:
        raise HTTPException(status_code=403, detail="User not found.")

    room_dict = asdict(room)
    await rds.set(f"room:{room.room_id}", json.dumps(room_dict))
    return

# 게임 내에서 발생하는 WebSocket 메시지를 처리하는 핵심 함수
async def publish_to_custom_room(room_id: int, message: dict):
    await rds.publish(f"room:{room_id}", json.dumps(message))

# 구독된 redis의 특정 id로부터 json을 받고 그걸 웹소캣으로 발송
async def pubsub_listener(room_id):
    pubsub = rds.pubsub()
    await pubsub.subscribe(f"room:{room_id}")
    async for msg in pubsub.listen():
        if msg:
            data = json.loads(msg)
            for ws in custom_game_rooms[room_id]:
                await ws.send_json(data)


