from app.database import engine, Base
from app.models import Playlist, Track, PlaylistTrack, User, Room, Participant, TrackProposal, Vote

Base.metadata.create_all(engine)
