from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.room import Room
    from app.models.vote import Vote
    from app.models.track_proposal import TrackProposal


class Participant(Base):
    __tablename__ = "participants"
    __table_args__ = (
        UniqueConstraint("room_id", "username", name="uq_participant_room_username"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50))
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"))
    role: Mapped[str] = mapped_column(String(10))  # "host" ou "guest"
    joined_at: Mapped[str] = mapped_column(
        String, server_default=func.now()
    )

    room: Mapped["Room"] = relationship(
        back_populates="participants",
        foreign_keys=[room_id],
    )
    votes: Mapped[list["Vote"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )
    proposals: Mapped[list["TrackProposal"]] = relationship(
        back_populates="proposer",
        cascade="all, delete-orphan",
    )
