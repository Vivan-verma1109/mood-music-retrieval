from fastapi import FastAPI
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

class QueryRequest(BaseModel):
    mood: str
    top_k: int = 10
    language: Optional[str] = None
    artists: Optional[list[str]] = None

@app.post("/query")
def run_query(req: QueryRequest):
    results = query(
        mood_text=req.mood,
        top_k=req.top_k,
        language=req.language,
    )
    # orient="records" gives [{name: ..., artists: ...}, ...] — standard JSON list format
    return results.to_dict(orient="records")
