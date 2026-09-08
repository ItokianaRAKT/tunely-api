import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.room import Room
from app.models.participant import Participant
from app.schemas.room import RoomCreate, RoomJoin, Room, RoomDetail, Participant as ParticipantSchema

router = APIRouter(
    prefix="/rooms",
    tags=["rooms"],
)


def generate_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def get_unique_code(db: Session) -> str:
    for _ in range(20):
        code = generate_code()
        exists = db.scalar(select(Room).where(Room.code == code))
        if not exists:
            return code
    raise HTTPException(status_code=500, detail="Could not generate unique code")


def get_current_participant(code: str, username: str, db: Session) -> Participant:
    room = db.scalar(select(Room).where(Room.code == code))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    participant = db.scalar(
        select(Participant)
        .where(Participant.room_id == room.id)
        .where(Participant.username == username)
    )
    if not participant:
        raise HTTPException(status_code=403, detail="You are not in this room")

    return participant


@router.post("/", response_model=Room, status_code=201)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    code = get_unique_code(db)

    new_room = Room(name=room.name, code=code, is_active=True)
    db.add(new_room)
    db.flush()

    host = Participant(username="host", room_id=new_room.id, role="host")
    db.add(host)
    db.flush()

    new_room.created_by = host.id
    db.commit()
    db.refresh(new_room)
    return new_room


@router.get("/{code}", response_model=RoomDetail)
def get_room(code: str, username: str = Query(...), db: Session = Depends(get_db)):
    participant = get_current_participant(code, username, db)

    room = db.scalar(select(Room).where(Room.code == code))
    participants = db.scalars(
        select(Participant).where(Participant.room_id == room.id)
    ).all()

    return RoomDetail(
        id=room.id,
        name=room.name,
        code=room.code,
        is_active=room.is_active,
        created_by=room.created_by,
        participants=participants,
    )


@router.delete("/{code}")
def delete_room(
    code: str,
    username: str = Query(...),
    db: Session = Depends(get_db),
):
    participant = get_current_participant(code, username, db)

    room = db.scalar(select(Room).where(Room.code == code))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if room.created_by != participant.id:
        raise HTTPException(status_code=403, detail="Only the host can delete the room")

    db.delete(room)
    db.commit()
    return {"message": "Room deleted", "code": code}


@router.post("/{code}/join", response_model=ParticipantSchema, status_code=201)
def join_room(code: str, data: RoomJoin, db: Session = Depends(get_db)):
    room = db.scalar(select(Room).where(Room.code == code))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    if not room.is_active:
        raise HTTPException(status_code=400, detail="Room is no longer active")

    existing = db.scalar(
        select(Participant)
        .where(Participant.room_id == room.id)
        .where(Participant.username == data.username)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken in this room")

    participant = Participant(
        username=data.username,
        room_id=room.id,
        role="guest",
    )
    db.add(participant)
    db.commit()
    db.refresh(participant)
    return participant
