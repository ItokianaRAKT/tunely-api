from pydantic import BaseModel


class VoteResponse(BaseModel):
    message: str
    vote_count: int
