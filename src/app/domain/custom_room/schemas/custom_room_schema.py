from pydantic import BaseModel
from dataclasses import dataclass
from typing import Optional


class RoomCreateRequest(BaseModel):
    difficulty: int
    room_name: str
    use_language: str
    category: str


@dataclass
class UserState:
    user_id: int
    ready: bool = False
    screen_sharing: bool = False
    screen_sharing_ready: bool = False
    connected: bool = False

@dataclass
class CustomRoom:
    room_id: int
    maker: Optional[UserState]
    user: Optional[UserState]
    difficulty: int
    category: str
    use_language: str
    title: str
    is_gaming: bool

