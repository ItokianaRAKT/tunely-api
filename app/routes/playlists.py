from fastapi import APIRouter, HTTPException
from starlette.types import HTTPExceptionHandler
from app.database import DATABASE_URL
from app.schemas.playlist import PlaylistCreate,  Playlist

router = APIRouter(
    prefix="/playlists",
    tags=["playlists"]
)

@router.get("/", response_model=list[Playlist])
def get_playlists():
    return playlists

@router.get("/{playlist_id}", response_model=Playlist)
def get_playlist(playlist_id: int):
    for playlist in playlists:
        if playlist["id"]== playlist_id:
            return playlist
    raise HTTPException(
        status_code=404,
        detail="Playlist not found"
    )

@router.post("/")
def create_playlist(playlist: PlaylistCreate):
    new_playlist = {
        "id": len(playlists) + 1,
        "name": playlist.name,
        "description": playlist.description,
        "tracks": []
    }

    playlists.append(playlist)
    return playlist

@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int):
    for playlist in playlists:
        if playlist["id"] == playlist_id:
            playlists.remove(playlist)
            return {
                "message": "Playlist supprimée",
                "id": playlist_id
            }

    raise HTTPException(
        status_code=404,
        detail="Playlist not found"
    )

playlists = []
