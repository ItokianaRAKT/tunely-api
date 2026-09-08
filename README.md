# Tunely API

Real-time collaborative playlist API. Create rooms, share YouTube links, propose songs and vote — the most voted tracks play first.

## Tech Stack

- **Python 3.11+**
- **FastAPI** — async web framework
- **SQLAlchemy 2.0** — ORM (`mapped_column` style)
- **PostgreSQL** — database
- **psycopg 3** — PostgreSQL driver
- **Pydantic v2** — data validation
- **Uvicorn** — ASGI server

## Prerequisites

- Python 3.11 or higher
- PostgreSQL 12 or higher
- pip

## Installation

```bash
# Clone the repository
git clone https://github.com/ItokianaRAKT/tunely-api.git
cd tunely-api

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env with your PostgreSQL credentials
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_USER` | PostgreSQL user | — |
| `DATABASE_PASSWORD` | PostgreSQL password | — |
| `DATABASE_HOST` | Database host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |
| `DATABASE_NAME` | Database name | `tunely` |

## Database

Create the PostgreSQL database then initialize the tables:

```bash
# Create the database (if it doesn't exist)
createdb -U your_user tunely

# Initialize the tables
python -m app.init_db
```

## Running

```bash
# Development (with auto-reload)
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API is available at `http://127.0.0.1:8000`.

Interactive documentation is available at `http://127.0.0.1:8000/docs` (Swagger UI) or `http://127.0.0.1:8000/redoc` (ReDoc).

## Endpoints

### Playlists

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/playlists/` | List all playlists | `200` |
| `GET` | `/playlists/{id}` | Get a playlist by ID | `200` / `404` |
| `POST` | `/playlists/` | Create a playlist | `201` |
| `DELETE` | `/playlists/{id}` | Delete a playlist | `200` / `404` |

### Tracks

| Method | Endpoint | Description | Status |
|--------|----------|-------------|--------|
| `GET` | `/playlists/{id}/tracks` | Get tracks of a playlist (ordered by position) | `200` / `404` |
| `POST` | `/playlists/{id}/tracks` | Add a track to a playlist | `201` / `404` / `409` |
| `DELETE` | `/playlists/{id}/tracks/{track_id}` | Remove a track from a playlist | `200` / `404` |

### Request Examples

```bash
# Create a playlist
curl -X POST http://localhost:8000/playlists/ \
  -H "Content-Type: application/json" \
  -d '{"name": "Chill evening", "description": "Relaxed vibes"}'

# Add a track
curl -X POST http://localhost:8000/playlists/1/tracks \
  -H "Content-Type: application/json" \
  -d '{"title": "Daylight", "artist": "David Kushner", "youtube_id": "MoN9ql6Yymw"}'

# Get tracks of a playlist
curl http://localhost:8000/playlists/1/tracks

# Remove a track
curl -X DELETE http://localhost:8000/playlists/1/tracks/1
```

## Project Structure

```
tunely-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI entry point
│   ├── database.py          # DB config + session
│   ├── init_db.py           # Table initialization
│   ├── models/
│   │   ├── __init__.py
│   │   ├── playlist.py      # Playlist model
│   │   ├── track.py         # Track model
│   │   └── playlist_track.py # Junction table (many-to-many)
│   ├── routes/
│   │   ├── __init__.py
│   │   └── playlists.py     # Playlist + track CRUD routes
│   └── schemas/
│       ├── __init__.py
│       └── playlist.py      # Pydantic schemas (request/response)
├── .env.example             # Environment variables template
├── .gitignore
├── requirements.txt
└── README.md
```
