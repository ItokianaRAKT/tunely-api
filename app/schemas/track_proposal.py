from pydantic import BaseModel


class TrackProposalCreate(BaseModel):
    title: str
    artist: str
    youtube_id: str


class TrackProposal(BaseModel):
    id: int
    title: str
    artist: str
    youtube_id: str
    vote_count: int
    proposed_by: int
    status: str

    class Config:
        from_attributes = True
