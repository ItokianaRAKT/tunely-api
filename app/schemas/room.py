from pydantic import BaseModel


class Participant(BaseModel):
    id: int
    username: str
    role: str

    class Config:
        from_attributes = True


class RoomCreate(BaseModel):
    name: str
    username: str


class RoomJoin(BaseModel):
    username: str


class Room(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    created_by: int | None = None

    class Config:
        from_attributes = True


class RoomDetail(Room):
    participants: list[Participant] = []
