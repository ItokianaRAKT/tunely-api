from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.participant import Participant
    from app.models.room import Room
    from app.models.vote import Vote


class TrackProposal(Base):
    __tablename__ = "track_proposals"

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    proposed_by: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    title: Mapped[str] = mapped_column(String(200))
    artist: Mapped[str] = mapped_column(String(200))
    youtube_id: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(
        String(10), default="queued"
    )  # queued/playing/played/skipped
    vote_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(
        String, server_default=func.now()
    )

    room: Mapped["Room"] = relationship(
        back_populates="proposals",
        foreign_keys=[room_id],
    )
    proposer: Mapped["Participant"] = relationship(
        back_populates="proposals",
        foreign_keys=[proposed_by],
    )
    votes: Mapped[list["Vote"]] = relationship(
        back_populates="proposal",
        cascade="all, delete-orphan",
    )
