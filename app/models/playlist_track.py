from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    playlist_id: Mapped[int] = mapped_column(
        ForeignKey("playlists.id"),
        primary_key=True
    )

    track_id: Mapped[int] = mapped_column(
        ForeignKey("tracks.id"),
        primary_key=True
    )

    position: Mapped[int]
