import json
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import SECRET_KEY, ALGORITHM
from app.database import SessionLocal
from app.models.room import Room
from app.models.participant import Participant
from app.models.track_proposal import TrackProposal
from app.models.user import User


router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, code: str, username: str):
        await websocket.accept()
        if code not in self.active_connections:
            self.active_connections[code] = {}
        self.active_connections[code][username] = websocket

    def disconnect(self, code: str, username: str):
        if code in self.active_connections:
            self.active_connections[code].pop(username, None)
            if not self.active_connections[code]:
                del self.active_connections[code]

    async def broadcast(self, code: str, event: str, data: Any):
        if code not in self.active_connections:
            return
        message = json.dumps({"event": event, "data": data})
        for ws in self.active_connections[code].values():
            try:
                await ws.send_text(message)
            except Exception:
                pass


manager = ConnectionManager()


def get_user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError, TypeError):
        return None
    return db.scalar(select(User).where(User.id == user_id))


@router.websocket("/rooms/{code}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    code: str,
    token: str = Query(...),
):
    db = SessionLocal()
    try:
        user = get_user_from_token(token, db)
        if not user:
            await websocket.close(code=4001, reason="Invalid token")
            return

        room = db.scalar(select(Room).where(Room.code == code))
        if not room:
            await websocket.close(code=4004, reason="Room not found")
            return

        participant = db.scalar(
            select(Participant)
            .where(Participant.room_id == room.id)
            .where(Participant.username == user.username)
        )
        if not participant:
            await websocket.close(code=4003, reason="You are not in this room")
            return

        username = user.username
        await manager.connect(websocket, code, username)
        await manager.broadcast(code, "participant_joined", {
            "username": username,
            "role": participant.role,
        })

        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            event = msg.get("event")
            data = msg.get("data", {})

            if event == "like":
                await handle_like(code, username, data, db)
            elif event == "unlike":
                await handle_unlike(code, username, data, db)
            elif event == "propose_track":
                await handle_propose(code, username, data, db)
            elif event == "skip":
                await handle_skip(code, username, db)

    except WebSocketDisconnect:
        manager.disconnect(code, username)
        await manager.broadcast(code, "participant_left", {"username": username})
    finally:
        db.close()


async def handle_like(code: str, username: str, data: dict, db: Session):
    track_id = data.get("track_id")
    if not track_id:
        return

    room = db.scalar(select(Room).where(Room.code == code))
    participant = db.scalar(
        select(Participant)
        .where(Participant.room_id == room.id)
        .where(Participant.username == username)
    )

    proposal = db.scalar(
        select(TrackProposal)
        .where(TrackProposal.id == track_id)
        .where(TrackProposal.room_id == room.id)
        .where(TrackProposal.status == "queued")
    )
    if not proposal:
        return

    from app.models.vote import Vote
    existing = db.scalar(
        select(Vote)
        .where(Vote.proposal_id == track_id)
        .where(Vote.user_id == participant.id)
    )
    if existing:
        return

    vote = Vote(proposal_id=track_id, user_id=participant.id)
    db.add(vote)
    proposal.vote_count += 1
    db.commit()

    queue = db.scalars(
        select(TrackProposal)
        .where(TrackProposal.room_id == room.id)
        .where(TrackProposal.status == "queued")
        .order_by(TrackProposal.vote_count.desc(), TrackProposal.created_at.asc())
    ).all()

    await manager.broadcast(code, "vote_changed", {
        "track_id": track_id,
        "vote_count": proposal.vote_count,
        "username": username,
    })
    await manager.broadcast(code, "queue_updated", {
        "tracks": [{"id": t.id, "title": t.title, "vote_count": t.vote_count} for t in queue]
    })


async def handle_unlike(code: str, username: str, data: dict, db: Session):
    track_id = data.get("track_id")
    if not track_id:
        return

    room = db.scalar(select(Room).where(Room.code == code))
    participant = db.scalar(
        select(Participant)
        .where(Participant.room_id == room.id)
        .where(Participant.username == username)
    )

    from app.models.vote import Vote
    vote = db.scalar(
        select(Vote)
        .where(Vote.proposal_id == track_id)
        .where(Vote.user_id == participant.id)
    )
    if not vote:
        return

    proposal = db.scalar(select(TrackProposal).where(TrackProposal.id == track_id))
    proposal.vote_count -= 1
    db.delete(vote)
    db.commit()

    queue = db.scalars(
        select(TrackProposal)
        .where(TrackProposal.room_id == room.id)
        .where(TrackProposal.status == "queued")
        .order_by(TrackProposal.vote_count.desc(), TrackProposal.created_at.asc())
    ).all()

    await manager.broadcast(code, "vote_changed", {
        "track_id": track_id,
        "vote_count": proposal.vote_count,
        "username": username,
    })
    await manager.broadcast(code, "queue_updated", {
        "tracks": [{"id": t.id, "title": t.title, "vote_count": t.vote_count} for t in queue]
    })


async def handle_propose(code: str, username: str, data: dict, db: Session):
    room = db.scalar(select(Room).where(Room.code == code))
    participant = db.scalar(
        select(Participant)
        .where(Participant.room_id == room.id)
        .where(Participant.username == username)
    )

    duplicate = db.scalar(
        select(TrackProposal)
        .where(TrackProposal.room_id == room.id)
        .where(TrackProposal.youtube_id == data.get("youtube_id"))
        .where(TrackProposal.status == "queued")
    )
    if duplicate:
        return

    proposal = TrackProposal(
        room_id=room.id,
        proposed_by=participant.id,
        title=data.get("title", ""),
        artist=data.get("artist", ""),
        youtube_id=data.get("youtube_id", ""),
        status="queued",
        vote_count=0,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)

    await manager.broadcast(code, "track_added", {
        "id": proposal.id,
        "title": proposal.title,
        "artist": proposal.artist,
        "youtube_id": proposal.youtube_id,
        "vote_count": proposal.vote_count,
        "proposed_by": participant.username,
    })


async def handle_skip(code: str, username: str, db: Session):
    room = db.scalar(select(Room).where(Room.code == code))
    participant = db.scalar(
        select(Participant)
        .where(Participant.room_id == room.id)
        .where(Participant.username == username)
    )
    if participant.role != "host":
        return

    if room.current_track_id:
        current = db.scalar(
            select(TrackProposal).where(TrackProposal.id == room.current_track_id)
        )
        if current:
            current.status = "played"

    queue = db.scalars(
        select(TrackProposal)
        .where(TrackProposal.room_id == room.id)
        .where(TrackProposal.status == "queued")
        .order_by(TrackProposal.vote_count.desc(), TrackProposal.created_at.asc())
    ).all()

    next_track = None
    if queue:
        next_track = queue[0]
        next_track.status = "playing"
        room.current_track_id = next_track.id
    else:
        room.current_track_id = None

    db.commit()

    await manager.broadcast(code, "current_track_changed", {
        "id": room.current_track_id,
        "title": next_track.title if room.current_track_id else None,
        "artist": next_track.artist if room.current_track_id else None,
        "youtube_id": next_track.youtube_id if room.current_track_id else None,
    })
