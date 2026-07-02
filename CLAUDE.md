# Multimodal Mood-Based Music Retrieval

## Working Rules
- Before adding anything new (endpoint, function, config key, UI component), ask the user where they think it should live and why — let them reason through the architecture first.

---

## Project Goal
Build a system that takes a natural language mood description ("I'm feeling melancholic and introspective")
and returns a ranked playlist by combining:
1. **Emotional clusters** — songs grouped by audio features into emotional neighborhoods
2. **Lyrics semantics** — SBERT embeddings of song lyrics matched against the mood query
3. **Popularity signal** — Last.fm listener counts to surface recognizable songs

---

## Architecture

```
User mood query (text) + optional genre / language / artist filters
        ↓
   SBERT embedding
        ↓
  cluster routing (genre → GENRE_CLUSTERS, or keyword match, or lyric centroid fallback)
        ↓
  candidate song pool filtered by language + artist
        ↓
  lyric + audio cosine similarity scoring
        ↓
  top 50 → Last.fm listener count re-ranking (+ genre tag boost)
        ↓
  Spotify availability check
        ↓
  Ranked playlist (top_k results)
```

## Pipeline Stages

### Stage 1 — Emotional Clustering
- Input: audio features (valence, energy, tempo, acousticness, danceability)
- Method: KMeans (8 clusters) on normalized features
- Output: 8 clusters — Chill/Acoustic, Euphoric/Party, Angry/Intense, Moody/Melancholic, Sunny/Relaxed, Rap/Rock, Sad/Introspective, Dark/R&B
- Labels assigned manually after inspecting cluster centroids

### Stage 2 — Lyric Embedding
- Input: lyrics text per song
- Method: paraphrase-multilingual-mpnet-base-v2 SBERT (multilingual, 768-dim), run on GPU (RTX 5070, WSL2)
- Output: 845k × 768 embedding matrix + FAISS IndexFlatIP for cosine similarity search
- Run in WSL: `cd ~/moodml && python3 Stage2Embeddings/embed.py`

### Stage 3 — Projection Layer (built, not used)
- Trained Ridge regression (768 → 5), R² ~0.2 across all features
- Dropped: poor R² caused wrong cluster routing ("melancholic" → Angry/Intense)
- Replaced by: lyric-space centroid cosine similarity for cluster routing
- File kept at archive/projection.pkl for future MLP experiments

### Stage 4 — Fusion & Ranking
- Cluster routing (three strategies, in priority order):
  1. UI genre → `GENRE_CLUSTERS` direct lookup (e.g. "hiphop" → clusters [5, 7])
  2. Keyword match against `cluster_tags` in config.py
  3. Lyric centroid fallback: cosine sim between query embedding and per-cluster centroids
- Language filter: ISO 639-1 code matched against `language` column (langdetect)
- Artist filter: substring match against `artists` column (case-insensitive)
- Candidate scoring: α * audio_sim + (1-α) * lyric_sim (α=0.3)
- Re-ranking: top 50 candidates re-ranked with Last.fm listener count
  - `final_score = lyric_score * (1 + 0.3 * listeners_norm)`
  - Songs with < 100k listeners filtered out
  - Genre tag boost: 3x multiplier if Last.fm artist tags match genre aliases
  - Artist listener counts cached to `backend/artist_cache.json` (persists across restarts)
- Spotify availability check: verifies top candidates exist on Spotify via search API

---

## Data
- Source: Kaggle Spotify dataset
- Raw: 955,307 songs
- After dedup (case-insensitive name+artist): 845,340 songs
- Columns: id, name, album_name, artists, danceability, energy, key, loudness, mode,
  speechiness, acousticness, instrumentalness, liveness, valence, tempo, duration_ms,
  lyrics, cluster, mood

## Audio Features
- valence — how happy/positive it sounds (0 to 1)
- energy — intensity/power of the track (0 to 1)
- tempo — BPM
- acousticness — how acoustic vs. electronic (0 to 1)
- danceability — how suitable for dancing (0 to 1)

## API Notes
- **Spotify Web API (Feb 2026)**: batch tracks endpoint (GET /tracks) removed, popularity field removed. Used only for availability check via search.
- **Last.fm API**: free, no OAuth for read calls. Used for listener counts and genre tags via artist.getInfo. Key in .env as LASTFM_API_KEY.

---

## Milestones
1. [x] Dataset acquired and columns inspected
2. [x] Audio features normalized, emotional clusters built and labeled (8 KMeans clusters)
3. [x] Lyrics embedded with SBERT on GPU, FAISS index built
4. [x] Projection layer trained (Ridge 768→5) — dropped in favor of lyric centroid routing
5. [x] End-to-end query → cluster filter → lyric rerank working
6. [x] Codebase restructured into backend/ folder
7. [x] FastAPI api.py at root exposing /query endpoint
8. [x] React frontend in frontend/ with inputs for mood, artist, genre, language, top_k
9. [ ] Restore audio similarity signal (KMeans centroid cosine sim in audio space)
10. [ ] Qualitative evaluation + fusion weight tuning
11. [ ] Genre hard filter (Last.fm track.getTopTags) — replace current score boost
12. [ ] Spotify OAuth + PostgreSQL (SQLAlchemy) for token storage
13. [ ] Spotify playlist export (POST /me/playlists)
14. [ ] Filter out user's liked songs from results
15. [ ] Release year / era filtering
16. [ ] Semantic cluster routing (SBERT embeddings of cluster descriptions, replaces keyword lists)

---

## Decisions & Rationale
- **paraphrase-multilingual-mpnet-base-v2**: multilingual, 768-dim, fast at batch 128 on RTX 5070 (~28 min for 955k songs). bge-m3 tried first but hung at batch 32.
- **Lyric centroid routing over projection layer**: projection layer (R²~0.2) routed "melancholic" → Angry/Intense. Lyric centroid cosine sim routes correctly.
- **GENRE_CLUSTERS for UI genre**: direct genre → cluster mapping bypasses keyword matching entirely, more reliable than inferring genre from mood text.
- **Last.fm over Spotify**: Spotify removed popularity field and batch tracks endpoint Feb 2026. Last.fm has listener counts, free, no quota issues.
- **File-based Last.fm artist cache**: in-memory dict persisted to artist_cache.json so listener counts survive server restarts.
- **Lazy Last.fm fetch**: only fetch for top 50 candidates per query. ~50 API calls, under 5 seconds.
- **Dedup on case-insensitive name+artist**: removed 110k duplicates. Embeddings and FAISS index filtered in sync.
- **Artist filter via UI input**: extracting artist names from free-text query is fragile; dedicated input box in the React UI is cleaner.
- **Genre as score boost (current)**: pending hard filter via Last.fm track.getTopTags; 3x boost stays until then.
- **React over Gradio**: chosen for long-term flexibility — Spotify OAuth, playlist export, liked songs filter all require a real frontend.
- **PostgreSQL over SQLite**: chosen for flexibility as the project grows (user data, playlists, query history).
- **Not collaborative filtering**: no user interaction data; content-based + query-based only.

## Stack
- **Backend**: FastAPI (Python), PostgreSQL + SQLAlchemy (planned, for OAuth token storage)
- **Frontend**: React (Vite)
- **ML pipeline**: lives in backend/ — numpy, pandas, SBERT, FAISS, scikit-learn

## Non-Goals
- Training a music-specific language model
- Production deployment
