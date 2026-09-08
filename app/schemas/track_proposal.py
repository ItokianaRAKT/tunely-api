from datetime import datetime

from pydantic import BaseModel


class TrackProposalCreate(BaseModel):
    title: str
    artist: str
    youtube_id: str


class TrackProposal(BaseModel):
    id: int
    room_id: int
    title: str
    artist: str
    youtube_id: str
    vote_count: int
    proposed_by: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
