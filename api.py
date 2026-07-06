# FastAPI server — exposes the /query and /feedback endpoints that the React frontend calls.
# Receives mood text + filters, runs the full retrieval pipeline, returns ranked songs.
import uuid
import time
import math
import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from backend.Stage4Fusion.fusion import query

app = FastAPI()

# allow the React dev server to call this API (browsers block cross-origin requests by default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite's default port
    allow_methods=["*"],
    allow_headers=["*"],
)

# request_id -> {songs: per_song dict, expires_at: float}
_request_cache = {}
_CACHE_TTL = 60 * 30  # 30 minutes

_FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'backend', 'feedback.jsonl')

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
    _request_cache[request_id] = {
        "songs": per_song,
        "expires_at": time.time() + _CACHE_TTL,
    }
    records = results.to_dict(orient="records")
    return {"request_id": request_id, "results": records}

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
