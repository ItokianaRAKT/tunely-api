from app.database import engine, Base
from app.models import Playlist

Base.metadata.create_all(engine)
