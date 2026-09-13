-- Tunely seed data
-- Default test user + sample playlist

BEGIN;

-- Test user (password: password123)
INSERT INTO users (email, username, hashed_password)
VALUES ('test@tunely.com', 'testuser', '$2b$12$ntR6/1zQxHuNK7YLUEpRRehcPX4a43WDmnvfzxTZyUSUCx9/K2LeS');

-- Sample tracks
INSERT INTO tracks (title, artist, youtube_id) VALUES
    ('Daylight', 'David Kushner', 'MoN9ql6Yymw'),
    ('Escapism', 'RAYE', 'nCvjZCPzLJ8'),
    ('Blinding Lights', 'The Weeknd', '4NRXx6U8ABQ');

-- Sample playlist
INSERT INTO playlists (name, description) VALUES
    ('Chill Vibes', 'Ambiance détente'),
    ('Party Mix', 'Pour faire la fête');

-- Link tracks to playlists
INSERT INTO playlist_tracks (playlist_id, track_id, position) VALUES
    (1, 1, 0),
    (1, 2, 1),
    (2, 3, 0);

COMMIT;
