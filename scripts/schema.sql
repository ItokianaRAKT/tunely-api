-- Tunely database schema
-- Generated from SQLAlchemy models

BEGIN;

-- Users
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Playlists
CREATE TABLE IF NOT EXISTS playlists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Tracks
CREATE TABLE IF NOT EXISTS tracks (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    artist VARCHAR(200) NOT NULL,
    youtube_id VARCHAR(20) NOT NULL
);

-- Rooms (without FKs first)
CREATE TABLE IF NOT EXISTS rooms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(6) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    current_track_id INTEGER,
    created_by INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Participants
CREATE TABLE IF NOT EXISTS participants (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL DEFAULT 'guest',
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(room_id, username)
);

-- Track proposals
CREATE TABLE IF NOT EXISTS track_proposals (
    id SERIAL PRIMARY KEY,
    room_id INTEGER NOT NULL REFERENCES rooms(id) ON DELETE CASCADE,
    proposed_by INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    title VARCHAR(200) NOT NULL,
    artist VARCHAR(200) NOT NULL,
    youtube_id VARCHAR(20) NOT NULL,
    status VARCHAR(10) DEFAULT 'queued',
    vote_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Votes
CREATE TABLE IF NOT EXISTS votes (
    id SERIAL PRIMARY KEY,
    proposal_id INTEGER NOT NULL REFERENCES track_proposals(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES participants(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(proposal_id, user_id)
);

-- Playlist tracks (junction)
CREATE TABLE IF NOT EXISTS playlist_tracks (
    playlist_id INTEGER NOT NULL REFERENCES playlists(id) ON DELETE CASCADE,
    track_id INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
    position INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (playlist_id, track_id)
);

-- Add circular FKs on rooms
ALTER TABLE rooms ADD FOREIGN KEY (current_track_id) REFERENCES track_proposals(id);
ALTER TABLE rooms ADD FOREIGN KEY (created_by) REFERENCES participants(id);

COMMIT;
