from fastapi import FastAPI
from app.routes.playlists import router as playlist_router
from app.routes.rooms import router as rooms_router
from app.routes.ws import router as ws_router

app = FastAPI(
    title="Tunely API",
    description="API de playlist collaborative en temps réel",
    version="0.2.0",
)

app.include_router(playlist_router)
app.include_router(rooms_router)
app.include_router(ws_router)


@app.get("/")
def root():
    return {
        "name": "Tunely API",
        "status": "online",
    }
