from pydoc import describe

from pydantic import BaseModel

class PlaylistCreate(BaseModel):
    name: str
    description: str | None = None

class Playlist(BaseModel):
    id: int
    name: str
    description: str | None = None
    tracks: list
