from pydantic import BaseModel, ConfigDict


class UserResponseDto(BaseModel):
    user_id: int
    email: str
    username: str
    nickname: str

    model_config = {"from_attributes": True}


class UserRequestDto(BaseModel):
    user_id: int
    email: str
    username: str
    nickname: str

    model_config = ConfigDict(from_attributes=True)


class UserDto(BaseModel):
    user_id: int
    email: str
    username: str
    nickname: str

    model_config = ConfigDict(from_attributes=True)
