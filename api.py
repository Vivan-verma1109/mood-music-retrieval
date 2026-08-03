# FastAPI server — exposes the /query, /page, and /feedback endpoints that the React frontend calls.
# Receives mood text + filters, runs the full retrieval pipeline, returns ranked songs.
import uuid
import time
import math
import json
import os
import numpy as np
import requests
import datetime
from backend.auth.db import SessionLocal
from backend.auth.models import SpotifyToken
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from backend.Stage4Fusion.fusion import query
from backend.Stage0Data.years import years_cache
from backend.auth.routes import router as auth_router
from backend.auth.db import engine, Base
from backend.auth import models  # registers models so create_all sees them

app = FastAPI()
app.include_router(auth_router)
Base.metadata.create_all(bind=engine)  # creates spotify_tokens table if it doesn't exist

# allow the React dev server to call this API (browsers block cross-origin requests by default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_methods=["*"],
    allow_headers=["*"],
)

# set to True once loader.py has finished loading weights on startup
_ready = False

@app.on_event("startup")
async def startup():
    global _ready
    # loader.py runs on import (triggered by fusion.py), so weights are already in memory by now
    _ready = True

# reject all non-health requests until weights are loaded
@app.middleware("http")
async def readiness_gate(request: Request, call_next):
    if not _ready and request.url.path != "/health":
        return JSONResponse({"error": "loading"}, status_code=503)
    return await call_next(request)

@app.get("/health")
def health():
    return {"ready": _ready}

# request_id -> {songs: per_song dict, expires_at: float}
_request_cache = {}
_CACHE_TTL = 60 * 30  # 30 minutes

_FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'backend', 'Testing', 'data', 'feedback.jsonl')

class QueryRequest(BaseModel):
    mood: str
    top_k: int = 10
    language: Optional[str] = None
    genre: Optional[str] = None
    artist: Optional[str] = None

class FeedbackRequest(BaseModel):
    request_id: str
    song_id: str
    rating: str  # "good" or "bad"

class PageRequest(BaseModel):
    request_id: str
    offset: int

class LikeRequest(BaseModel):
    spotify_id: str


# runs the full pipeline and returns the first 10 songs, caches the full pool for paging
@app.post("/query")
def run_query(req: QueryRequest):
    results, per_song = query(
        mood_text=req.mood,
        top_k=req.top_k,
        language=req.language,
        genre=req.genre,
        artist=req.artist,
    )
    request_id = str(uuid.uuid4())
    # convert NaN to None so json serialization doesn't blow up
    records = [{k: (None if isinstance(v, float) and np.isnan(v) else v) for k, v in row.items()} for row in results.to_dict(orient="records")]
    _request_cache[request_id] = {
        "songs": per_song,
        "pool": records, 
        "expires_at": time.time() + _CACHE_TTL,
    }
    # 10 first images
    first_page = records[:10]
    for r in first_page:
        r['image'] = (years_cache.get(r['song_id']) or {}).get('image')
    return {"request_id": request_id, "results": first_page}

# saves a thumbs up/down rating for a song to feedback.jsonl
@app.post("/feedback")
def submit_feedback(req: FeedbackRequest):
    entry = _request_cache.get(req.request_id)
    if not entry or time.time() > entry["expires_at"]:
        _request_cache.pop(req.request_id, None)
        raise HTTPException(status_code=410, detail="Request expired")

    song_meta = entry["songs"].get(req.song_id)
    if not song_meta:
        raise HTTPException(status_code=404, detail="Song not found in request")

    record = {**song_meta, "song_id": req.song_id, "rating": req.rating, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

    assert math.isclose(
        record["fused_score"] * (1 + record["listener_weight"] * record["listeners_norm"]) * (record["boost_multiplier"] if record["genre_boost_fired"] else 1),
        record["final_score"],
        rel_tol=1e-5,
    ), "Invariant check failed"

    with open(_FEEDBACK_FILE, 'a') as f:
        f.write(json.dumps(record) + '\n')

    return {"status": "ok"}

# slices the next 10 songs from the cached pool without re-running the pipeline
@app.post("/page")
def next_page(req: PageRequest):
    entry = _request_cache.get(req.request_id)
    if not entry or time.time() > entry["expires_at"]:
        _request_cache.pop(req.request_id, None)
        raise HTTPException(status_code=410, detail="Request expired")
    page = entry["pool"][req.offset: req.offset + 10]
    for r in page:
        r['image'] = (years_cache.get(r['song_id']) or {}).get('image')
    return {"results": page}



# gets the stored token, refreshes it if expired, returns the access token string
def _get_spotify_token():
    db = SessionLocal()
    token = db.query(SpotifyToken).first()
    if not token:
        db.close()
        raise HTTPException(status_code=401, detail="Not connected to Spotify")
    if token.expires_at < datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None):
        resp = requests.post('https://accounts.spotify.com/api/token', data={
            'grant_type': 'refresh_token',
            'refresh_token': token.refresh_token,
        }, auth=(os.getenv('SPOTIFY_CLIENT_ID'), os.getenv('SPOTIFY_CLIENT_SECRET')))
        data = resp.json()
        token.access_token = data['access_token']
        token.expires_at = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) + datetime.timedelta(seconds=data['expires_in'])
        db.commit()
    access_token = token.access_token
    db.close()
    return access_token

@app.post("/like")
def like_song(req: LikeRequest):
    access_token = _get_spotify_token()
    resp = requests.put(
        f'https://api.spotify.com/v1/me/library?uris=spotify:track:{req.spotify_id}',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Spotify API error")
    return {"status": "ok"}

# removes a track from the user's spotify liked songs
@app.post("/unlike")
def unlike_song(req: LikeRequest):
    access_token = _get_spotify_token()
    resp = requests.delete(
        f'https://api.spotify.com/v1/me/library?uris=spotify:track:{req.spotify_id}',
        headers={'Authorization': f'Bearer {access_token}'},
    )
    if resp.status_code not in (200, 201):
        raise HTTPException(status_code=502, detail="Spotify API error")
    return {"status": "ok"}