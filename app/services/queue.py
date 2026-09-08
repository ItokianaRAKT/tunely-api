from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.track_proposal import TrackProposal


def get_queue(db: Session, room_id: int) -> list[TrackProposal]:
    """Return tracks ordered by vote_count DESC, then created_at ASC."""
    return list(
        db.scalars(
            select(TrackProposal)
            .where(TrackProposal.room_id == room_id)
            .where(TrackProposal.status == "queued")
            .order_by(TrackProposal.vote_count.desc(), TrackProposal.created_at.asc())
        ).all()
    )


def is_duplicate_in_queue(db: Session, room_id: int, youtube_id: str) -> bool:
    """Check if a YouTube ID already exists in the active queue."""
    existing = db.scalar(
        select(TrackProposal)
        .where(TrackProposal.room_id == room_id)
        .where(TrackProposal.youtube_id == youtube_id)
        .where(TrackProposal.status == "queued")
    )
    return existing is not None
