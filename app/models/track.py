from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.playlist import Playlist


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    artist: Mapped[str] = mapped_column(String(200))
    youtube_id: Mapped[str] = mapped_column(String(20))

    playlists: Mapped[list["Playlist"]] = relationship(
        secondary="playlist_tracks"
    )
