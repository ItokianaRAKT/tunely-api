from pydantic import BaseModel


class TrackBase(BaseModel):
    title: str
    artist: str
    youtube_id: str


class TrackCreate(TrackBase):
    pass


class Track(TrackBase):
    id: int

    class Config:
        from_attributes = True


class PlaylistCreate(BaseModel):
    name: str
    description: str | None = None


class Playlist(BaseModel):
    id: int
    name: str
    description: str | None = None
    tracks: list[Track] = []

    class Config:
        from_attributes = True
