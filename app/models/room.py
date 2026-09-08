from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.participant import Participant
    from app.models.track_proposal import TrackProposal


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    code: Mapped[str] = mapped_column(String(6), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    current_track_id: Mapped[int | None] = mapped_column(
        ForeignKey("track_proposals.id"), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("participants.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    participants: Mapped[list["Participant"]] = relationship(
        back_populates="room",
        foreign_keys="Participant.room_id",
        cascade="all, delete-orphan",
    )
    proposals: Mapped[list["TrackProposal"]] = relationship(
        back_populates="room",
        foreign_keys="TrackProposal.room_id",
        cascade="all, delete-orphan",
    )
    current_track: Mapped["TrackProposal | None"] = relationship(
        foreign_keys=[current_track_id],
        post_update=True,
    )
