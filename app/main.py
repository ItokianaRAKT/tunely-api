from fastapi import FastAPI
from app.routes.playlists import router as playlist_router

app = FastAPI(
    title="Tunely API",
    description="API de playlist collaborative en temps réel",
    version="0.1.0",
)

app.include_router(playlist_router)

@app.get("/")
def root():
    return {
        "name": "Tunely API",
        "status": "online"
    }
