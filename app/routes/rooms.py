import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.room import Room
from app.models.participant import Participant
from app.models.track_proposal import TrackProposal
from app.models.vote import Vote
from app.schemas.room import RoomCreate, RoomJoin, Room as RoomSchema, RoomDetail, Participant as ParticipantSchema
from app.schemas.track_proposal import TrackProposalCreate, TrackProposal as TrackProposalSchema
from app.schemas.vote import VoteResponse

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


@router.post("/", response_model=RoomSchema, status_code=201)
def create_room(room: RoomCreate, db: Session = Depends(get_db)):
    code = get_unique_code(db)

    new_room = Room(name=room.name, code=code, is_active=True)
    db.add(new_room)
    db.flush()

    host = Participant(username=room.username, room_id=new_room.id, role="host")
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

    room.created_by = None
    db.flush()
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


@router.get("/{code}/tracks", response_model=list[TrackProposalSchema])
def get_room_tracks(
    code: str,
    username: str = Query(...),
    db: Session = Depends(get_db),
):
    participant = get_current_participant(code, username, db)

    room = db.scalar(select(Room).where(Room.code == code))
    tracks = db.scalars(
        select(TrackProposal)
        .where(TrackProposal.room_id == room.id)
        .where(TrackProposal.status == "queued")
        .order_by(TrackProposal.vote_count.desc(), TrackProposal.created_at.asc())
    ).all()
    return tracks


@router.post("/{code}/tracks", response_model=TrackProposalSchema, status_code=201)
def propose_track(
    code: str,
    track: TrackProposalCreate,
    username: str = Query(...),
    db: Session = Depends(get_db),
):
    participant = get_current_participant(code, username, db)

    room = db.scalar(select(Room).where(Room.code == code))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    duplicate = db.scalar(
        select(TrackProposal)
        .where(TrackProposal.room_id == room.id)
        .where(TrackProposal.youtube_id == track.youtube_id)
        .where(TrackProposal.status == "queued")
    )
    if duplicate:
        raise HTTPException(status_code=409, detail="Track already in queue")

    proposal = TrackProposal(
        room_id=room.id,
        proposed_by=participant.id,
        title=track.title,
        artist=track.artist,
        youtube_id=track.youtube_id,
        status="queued",
        vote_count=0,
    )
    db.add(proposal)
    db.commit()
    db.refresh(proposal)
    return proposal


@router.delete("/{code}/tracks/{track_id}")
def remove_track(
    code: str,
    track_id: int,
    username: str = Query(...),
    db: Session = Depends(get_db),
):
    participant = get_current_participant(code, username, db)

    proposal = db.scalar(
        select(TrackProposal)
        .where(TrackProposal.id == track_id)
        .where(TrackProposal.room_id == participant.room_id)
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Track not found")

    if proposal.proposed_by != participant.id:
        raise HTTPException(status_code=403, detail="Only the proposer can remove this track")

    if proposal.vote_count > 0:
        raise HTTPException(status_code=400, detail="Cannot remove a track that has votes")

    db.delete(proposal)
    db.commit()
    return {"message": "Track removed", "track_id": track_id}


@router.post("/{code}/tracks/{track_id}/like", response_model=VoteResponse)
def like_track(
    code: str,
    track_id: int,
    username: str = Query(...),
    db: Session = Depends(get_db),
):
    participant = get_current_participant(code, username, db)

    proposal = db.scalar(
        select(TrackProposal)
        .where(TrackProposal.id == track_id)
        .where(TrackProposal.room_id == participant.room_id)
        .where(TrackProposal.status == "queued")
    )
    if not proposal:
        raise HTTPException(status_code=404, detail="Track not found in queue")

    existing_vote = db.scalar(
        select(Vote)
        .where(Vote.proposal_id == track_id)
        .where(Vote.user_id == participant.id)
    )
    if existing_vote:
        raise HTTPException(status_code=409, detail="Already liked this track")

    vote = Vote(proposal_id=track_id, user_id=participant.id)
    db.add(vote)
    proposal.vote_count += 1
    db.commit()
    return VoteResponse(message="Liked", vote_count=proposal.vote_count)


@router.delete("/{code}/tracks/{track_id}/like", response_model=VoteResponse)
def unlike_track(
    code: str,
    track_id: int,
    username: str = Query(...),
    db: Session = Depends(get_db),
):
    participant = get_current_participant(code, username, db)

    vote = db.scalar(
        select(Vote)
        .where(Vote.proposal_id == track_id)
        .where(Vote.user_id == participant.id)
    )
    if not vote:
        raise HTTPException(status_code=404, detail="Like not found")

    proposal = db.scalar(
        select(TrackProposal)
        .where(TrackProposal.id == track_id)
    )
    proposal.vote_count -= 1
    db.delete(vote)
    db.commit()
    return VoteResponse(message="Unliked", vote_count=proposal.vote_count)


@router.get("/{code}/current")
def get_current_track(
    code: str,
    username: str = Query(...),
    db: Session = Depends(get_db),
):
    participant = get_current_participant(code, username, db)

    room = db.scalar(select(Room).where(Room.code == code))
    if not room or not room.current_track_id:
        return {"track": None}

    track = db.scalar(
        select(TrackProposal).where(TrackProposal.id == room.current_track_id)
    )
    if not track:
        return {"track": None}

    return {
        "track": {
            "id": track.id,
            "title": track.title,
            "artist": track.artist,
            "youtube_id": track.youtube_id,
            "vote_count": track.vote_count,
        }
    }


@router.post("/{code}/current/next")
def skip_to_next(
    code: str,
    username: str = Query(...),
    db: Session = Depends(get_db),
):
    participant = get_current_participant(code, username, db)

    if participant.role != "host":
        raise HTTPException(status_code=403, detail="Only the host can skip tracks")

    room = db.scalar(select(Room).where(Room.code == code))
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

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

    if room.current_track_id:
        return {
            "message": "Skipped to next track",
            "track": {
                "id": next_track.id,
                "title": next_track.title,
                "artist": next_track.artist,
                "youtube_id": next_track.youtube_id,
            },
        }
    else:
        return {"message": "No more tracks in queue", "track": None}
