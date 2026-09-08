from typing import TYPE_CHECKING

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.participant import Participant
    from app.models.track_proposal import TrackProposal


class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (
        UniqueConstraint("proposal_id", "user_id", name="uq_vote_proposal_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    proposal_id: Mapped[int] = mapped_column(ForeignKey("track_proposals.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("participants.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    proposal: Mapped["TrackProposal"] = relationship(
        back_populates="votes",
        foreign_keys=[proposal_id],
    )
    user: Mapped["Participant"] = relationship(
        back_populates="votes",
        foreign_keys=[user_id],
    )
