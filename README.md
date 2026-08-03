# Mood Moosic

A multimodal music retrieval system that takes a natural language mood description and returns a ranked playlist. Type "melancholic and rainy" or "music for a bbq" and get back songs that actually fit.

![React + FastAPI + SBERT + FAISS](https://img.shields.io/badge/stack-React%20%7C%20FastAPI%20%7C%20SBERT%20%7C%20FAISS-1db954?style=flat)

---

## How it works

```
mood query (text) + optional genre / language / artist filters
        ↓
   SBERT embedding (paraphrase-multilingual-mpnet-base-v2, 768-dim)
        ↓
  cluster routing — genre lookup or cosine sim against 13 cluster descriptions
        ↓
  LLM expansion gate — if routing confidence < 0.45, Claude Haiku rewrites
        the query into mood/audio vocabulary and re-routes
        ↓
  candidate pool filtered by language + artist
        ↓
  fusion score: 0.6 × audio_sim + 0.4 × lyric_sim
        ↓
  top 50 re-ranked by Last.fm listener count
        ↓
  ranked pool of 50 cached under request_id, paged 10 at a time
```

### Emotional clusters

845k songs grouped into 13 clusters via KMeans on 7 audio features (valence, energy, tempo, acousticness, danceability, speechiness, instrumentalness). Each cluster has a natural language description that's embedded at startup and used for cosine-similarity routing.

| # | Cluster |
|---|---------|
| 0 | Subdued mid-tempo pop/alternative — catch-all |
| 1 | Produced groove, R&B, dancehall, reggae |
| 2 | Warm vintage acoustic classics |
| 3 | Energetic instrumental electronic |
| 4 | Metal and hard rock with sung vocals |
| 5 | Euphoric party pop and dance |
| 6 | Melancholy modern songs |
| 7 | Extreme metal with harsh vocals |
| 8 | Organic roots, salsa, gospel, country |
| 9 | Calm quiet instrumental and ambient |
| 10 | Fast loud punk and ska |
| 11 | Hushed timeless ballads and torch songs |
| 12 | High energy mainstream rock/pop crossover |

### LLM expansion

For vague or pop-culture queries ("feels like Sonic the Hedgehog", "something like Drake"), the routing confidence score drops below 0.45 or lands on the catch-all cluster. In that case, Claude Haiku rewrites the query into mood and audio vocabulary before re-routing. Falls back silently if the API call fails.

---

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI (Python) |
| ML pipeline | SBERT, FAISS, scikit-learn, numpy, pandas |
| Frontend | React (Vite) |
| Database | PostgreSQL + SQLAlchemy (Spotify OAuth token storage) |
| Embeddings | paraphrase-multilingual-mpnet-base-v2 (768-dim, multilingual) |
| Popularity signal | Last.fm API (listener counts + genre tags) |
| LLM expansion | Claude Haiku (claude-haiku-4-5-20251001) |
| Spotify | OAuth 2.0, like/unlike via `/v1/me/library` |

---

## Dataset

- Source: Kaggle Spotify dataset
- 955,307 songs → 845,340 after case-insensitive dedup on (name, artist)
- Columns used: audio features, lyrics, cluster assignment, language

Lyric embeddings (845k × 768) and the FAISS index are generated separately and not included in the repo.

---

## Project structure

```
api.py                        # FastAPI server — /query, /page, /feedback, /like, /unlike, /health
backend/
  Stage0Data/                 # data loading, dedup, year/image cache
  Stage1Clustering/           # KMeans training and cluster assignment
  Stage2Embeddings/           # SBERT embedding script (run in WSL on GPU)
  Stage4Fusion/               # cluster routing, LLM expansion, fusion scoring, Last.fm reranking
    fusion.py                 # main pipeline entry point
    loader.py                 # loads model, embeddings, FAISS index at startup
    expand_query.py           # Claude Haiku expansion gate
  auth/                       # Spotify OAuth routes, PostgreSQL token storage
  Testing/                    # eval scripts, routing diagnostics, feedback log
  config.py                   # cluster descriptions, genre aliases, genre→cluster mappings
frontend/
  src/
    App.jsx                   # main UI — query form, card grid, Spotify connect/logout
    Bubbles.jsx               # animated background
docs/
  timeline.md                 # full decision log — what was tried, what was dropped and why
```

---

## Running locally

**Backend**
```bash
# from repo root
python -m uvicorn api:app --reload
```

Requires a `.env` with:
```
SPOTIFY_CLIENT_ID=...
SPOTIFY_CLIENT_SECRET=...
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8000/auth/callback
LASTFM_API_KEY=...
ANTHROPIC_API_KEY=...
DATABASE_URL=postgresql://...
```

**Frontend**
```bash
cd frontend
npm install
npm run dev
```

**Generating embeddings** (requires GPU, run in WSL)
```bash
cd ~/moodml && python3 Stage2Embeddings/embed.py
```

---

## Features

- Natural language mood query with optional genre, language, and artist filters
- 13-cluster emotional routing with semantic SBERT matching
- LLM fallback expansion for vague or pop-culture queries
- Multilingual support (langdetect on lyrics)
- Last.fm listener count re-ranking with genre tag boost
- Paged results (10 at a time) from a cached pool of 50
- Spotify OAuth — like/unlike songs directly from results
- Dark UI with album art, animated bubble background
- `/health` endpoint with startup readiness gate

---

## Decisions & what didn't work

The full decision log is in [`docs/timeline.md`](docs/timeline.md). Short version of things that were tried and dropped:

- **Projection layer (Ridge 768→5)**: R²~0.2, caused wrong cluster routing. Replaced by lyric centroid cosine similarity.
- **Keyword-based cluster routing**: brittle, missed synonyms entirely. Replaced by SBERT semantic routing.
- **Splitting cluster 0**: PCA showed one continuous blob (45% variance explained across 73k songs). Not splittable.
- **Spotify batch tracks endpoint**: 403s for dev apps as of Feb 2026. Switched to single-track lazy fetch.
- **Alpha tuning**: blind eval across 170 ratings at 4 alpha values showed P@10 was flat (0.41–0.45). Audio sim is ~0.96 flat within any cluster's candidate pool — it separates clusters from each other, not songs within a pool. Alpha set to 0.6 to reduce literal lyric matching.
