from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.room import Room
from app.models.track_proposal import TrackProposal
from app.services.queue import get_queue


def skip_to_next(db: Session, room: Room) -> TrackProposal | None:
    """Mark current track as played, set next as playing. Returns the new current track."""
    if room.current_track_id:
        current = db.scalar(
            select(TrackProposal).where(TrackProposal.id == room.current_track_id)
        )
        if current:
            current.status = "played"

    queue = get_queue(db, room.id)

    if queue:
        next_track = queue[0]
        next_track.status = "playing"
        room.current_track_id = next_track.id
        db.commit()
        return next_track
    else:
        room.current_track_id = None
        db.commit()
        return None
