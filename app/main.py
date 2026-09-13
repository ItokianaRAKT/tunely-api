from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.playlists import router as playlist_router
from app.routes.rooms import router as rooms_router
from app.routes.auth import router as auth_router
from app.routes.ws import router as ws_router

app = FastAPI(
    title="Tunely API",
    description="API de playlist collaborative en temps réel",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(playlist_router)
app.include_router(rooms_router)
app.include_router(ws_router)


@app.get("/")
def root():
    return {
        "name": "Tunely API",
        "status": "online",
    }
