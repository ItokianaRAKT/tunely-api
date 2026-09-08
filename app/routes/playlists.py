from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.playlist import Playlist as PlaylistModel
from app.models.track import Track as TrackModel
from app.models.playlist_track import PlaylistTrack
from app.schemas.playlist import (
    PlaylistCreate,
    Playlist,
    TrackCreate,
    Track,
)

router = APIRouter(
    prefix="/playlists",
    tags=["playlists"],
)


@router.get("/", response_model=list[Playlist])
def get_playlists(db: Session = Depends(get_db)):
    playlists = db.scalars(select(PlaylistModel)).all()
    return playlists


@router.get("/{playlist_id}", response_model=Playlist)
def get_playlist(playlist_id: int, db: Session = Depends(get_db)):
    playlist = db.get(PlaylistModel, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    return playlist


@router.post("/", response_model=Playlist, status_code=201)
def create_playlist(playlist: PlaylistCreate, db: Session = Depends(get_db)):
    new_playlist = PlaylistModel(
        name=playlist.name,
        description=playlist.description,
    )
    db.add(new_playlist)
    db.commit()
    db.refresh(new_playlist)
    return new_playlist


@router.delete("/{playlist_id}")
def delete_playlist(playlist_id: int, db: Session = Depends(get_db)):
    playlist = db.get(PlaylistModel, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    db.delete(playlist)
    db.commit()
    return {"message": "Playlist deleted", "id": playlist_id}


@router.get("/{playlist_id}/tracks", response_model=list[Track])
def get_playlist_tracks(playlist_id: int, db: Session = Depends(get_db)):
    playlist = db.get(PlaylistModel, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    rows = db.scalars(
        select(TrackModel)
        .join(PlaylistTrack, PlaylistTrack.track_id == TrackModel.id)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .order_by(PlaylistTrack.position)
    ).all()
    return rows


@router.post("/{playlist_id}/tracks", response_model=Track, status_code=201)
def add_track_to_playlist(
    playlist_id: int,
    track: TrackCreate,
    db: Session = Depends(get_db),
):
    playlist = db.get(PlaylistModel, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    existing = db.scalars(
        select(TrackModel).where(TrackModel.youtube_id == track.youtube_id)
    ).first()

    if existing:
        track_obj = existing
    else:
        track_obj = TrackModel(
            title=track.title,
            artist=track.artist,
            youtube_id=track.youtube_id,
        )
        db.add(track_obj)
        db.flush()

    already_in = db.scalars(
        select(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .where(PlaylistTrack.track_id == track_obj.id)
    ).first()

    if already_in:
        raise HTTPException(status_code=409, detail="Track already in playlist")

    next_pos = db.scalar(
        select(func.max(PlaylistTrack.position)).where(
            PlaylistTrack.playlist_id == playlist_id
        )
    ) or 0

    link = PlaylistTrack(
        playlist_id=playlist_id,
        track_id=track_obj.id,
        position=next_pos + 1,
    )
    db.add(link)
    db.commit()
    db.refresh(track_obj)
    return track_obj


@router.delete("/{playlist_id}/tracks/{track_id}")
def remove_track_from_playlist(
    playlist_id: int,
    track_id: int,
    db: Session = Depends(get_db),
):
    playlist = db.get(PlaylistModel, playlist_id)
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    link = db.scalars(
        select(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .where(PlaylistTrack.track_id == track_id)
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Track not in playlist")

    removed_position = link.position
    db.delete(link)

    db.execute(
        update(PlaylistTrack)
        .where(PlaylistTrack.playlist_id == playlist_id)
        .where(PlaylistTrack.position > removed_position)
        .values(position=PlaylistTrack.position - 1)
    )

    db.commit()
    return {"message": "Track removed", "track_id": track_id}
