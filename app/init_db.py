from app.database import engine, Base
from app.models import Playlist, Track, PlaylistTrack, Room, Participant, TrackProposal, Vote

Base.metadata.create_all(engine)
