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
  cluster routing (genre → GENRE_CLUSTERS, or semantic SBERT cosine sim against cluster descriptions)
        ↓
  LLM expansion gate (if top-1 cosine < 0.45 OR top cluster == 0, call Claude Haiku to rewrite query into mood/audio vocab, re-embed, re-route)
        ↓
  candidate song pool filtered by language + artist
        ↓
  lyric + audio cosine similarity scoring
        ↓
  top 50 → Last.fm listener count re-ranking (+ genre tag boost)
        ↓
  Ranked pool of 50 cached under request_id (paged 10 at a time via /page)
```

## Pipeline Stages

### Stage 1 — Emotional Clustering
- Input: audio features (valence, energy, tempo, acousticness, danceability, speechiness, instrumentalness)
- Method: KMeans (13 clusters) on normalized features
- Output: 13 clusters — Mixed Moody Catch-all (0), Laid-Back Grooves/Reggae/Hip-Hop (1), Vintage Acoustic Classics (2), Energetic Electronic/Instrumental (3), Mainstream Metal/Hard Rock (4), Euphoric Party Pop/Dance (5), Melancholy Modern Songs (6), Extreme/Harsh Heavy (7), Feel-Good Roots/Tropical (8), Calm Quiet Instrumental (9), Fast Loud Punk/Ska (10), Hushed Ballads/Torch Songs (11), High-Energy Rock/Pop Crossover (12)
- Labels assigned manually after inspecting centroids and sampling songs per cluster; cluster descriptions rewritten July 2026 as routing targets (see Decisions)

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
- Cluster routing (two strategies, in priority order):
  1. UI genre → `GENRE_CLUSTERS` direct lookup (e.g. "hiphop" → clusters [0, 3])
  2. Semantic SBERT cosine sim: query embedding vs cluster description embeddings (13×768), top 3 clusters selected
- Language filter: ISO 639-1 code matched against `language` column (langdetect)
- Artist filter: substring match against `artists` column (case-insensitive)
- Candidate scoring: α * audio_sim + (1-α) * lyric_sim (α=0.6 — bumped from 0.3 to reduce literal lyric matching)
- Re-ranking: top 50 candidates re-ranked with Last.fm listener count
  - `final_score = fused_score * (1 + 0.3 * listeners_norm)`
  - Songs with < 10 listeners filtered out
  - Genre tag boost: 5x multiplier if Last.fm artist tags match genre aliases
  - Artist listener counts cached to `backend/artist_cache.json` (persists across restarts)
- Full ranked pool of 50 cached under request_id for 30 min; paged 10 at a time via /page endpoint
- Spotify availability check removed — spotify_id from dataset used directly for links

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
- speechiness — detects spoken words; high = rap/spoken word, low = singing (0 to 1)
- instrumentalness — predicts absence of vocals; high = instrumental track (0 to 1)

## API Notes
- **Spotify Web API (Feb 2026)**: batch tracks endpoint (GET /tracks) 403s for dev apps. Single track endpoint (GET /tracks/{id}) works. Used lazily at query time to fetch release year + album art, cached to `backend/Testing/data/years_cache.json`.
- **Last.fm API**: free, no OAuth for read calls. Used for listener counts and genre tags via artist.getInfo. Key in .env as LASTFM_API_KEY.

---

## Milestones
1. [x] Dataset acquired and columns inspected
2. [x] Audio features normalized, emotional clusters built and labeled (8 KMeans clusters → retrained to 13 with 7 features)
3. [x] Lyrics embedded with SBERT on GPU, FAISS index built
4. [x] Projection layer trained (Ridge 768→5) — dropped in favor of lyric centroid routing
5. [x] End-to-end query → cluster filter → lyric rerank working
6. [x] Codebase restructured into backend/ folder
7. [x] FastAPI api.py at root exposing /query, /page, /feedback endpoints
8. [x] React frontend in frontend/ with inputs for mood, artist, genre, language; card grid UI with album art
9. [x] Retrained KMeans with 7 features (added speechiness + instrumentalness), 13 clusters
10. [x] Semantic cluster routing (SBERT embeddings of cluster descriptions, top 3 clusters)
11. [x] Blind eval — 170 hand-labeled ratings across 18 queries at 4 alpha values; alpha=0.3 confirmed, closed
12. [x] Cluster descriptions rewritten as routing targets — activity/context vocab added, 6/11 and 1/5 twin pairs fixed
13. [ ] Validate description rewrite: pairwise cosine matrix + sanity routing (backend/Testing/validate_descriptions.py)
14. [ ] Rerun eval_batch on same 18 queries, rate new songs only, record before/after precision on context queries
15. [ ] Instrumentalness threshold filter for "no lyrics" queries
16. [ ] Genre hard filter (Last.fm track.getTopTags) — replace current score boost
17. [x] Spotify OAuth + PostgreSQL (SQLAlchemy) for token storage
18. [ ] Spotify playlist export (POST /me/playlists)
19. [ ] Filter out user's liked songs from results
20. [x] Lazy year + album art fetch via Spotify GET /tracks/{id}, cached to years_cache.json
21. [x] Dark UI overhaul — Spotify-ish card grid, animated bubble background, centered layout
22. [x] /page endpoint for paging through cached pool without re-running pipeline
23. [ ] Release year / era filtering (needs years_cache to bulk up first)
24. [ ] Artist filter bypasses cluster routing entirely
25. [ ] Bulk year/image enrichment script for hot catalog songs
26. [x] LLM query expansion — fallback gate on low-confidence routing, Claude Haiku with 3-shot prompt, re-embeds expanded text
27. [x] Cluster 0 description rewrite — too broad, scores moderately against unrelated queries even after expansion

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
- **13 clusters over 8**: added speechiness + instrumentalness to feature set, allowing clean separation of hip-hop, metal, jazz/classical, and instrumental clusters. Silhouette analysis showed more headroom with 7 features.
- **Semantic cluster routing over keyword matching**: cluster_tags keyword lists missed synonyms and paraphrases. SBERT descriptions encode the full semantic neighborhood; top 3 clusters selected by cosine sim.
- **Top 3 clusters**: cluster 0 is a broad catch-all; selecting 3 instead of 2 gives better coverage without bloating the candidate pool.
- **Alpha=0.3 confirmed, closed**: blind eval (170 ratings, 18 queries, 4 alpha values 0/0.15/0.3/0.5) showed precision 0.41–0.45 across the full range; top-10 lists were mostly the same songs reordered. Not worth tuning further.
- **audio_sim flat within candidate pools**: audio_sim ~0.96 across all rating levels within a cluster's candidate pool — it doesn't discriminate between songs once they're in the same cluster. Audio features separate clusters from each other; after that, lyric similarity does the ranking work. This is why alpha barely matters.
- **Cluster descriptions as routing targets**: rewritten July 2026 after eval showed context/activity queries (lift heavy, bbq, study) hitting 0–25% precision vs 75–90% for mood vocabulary queries. Root cause: original descriptions had no activity/context vocab so SBERT had nothing to match "songs to lift to" against. New structure: genre/sound + mood + activity/context per description, all 13 generated contrastively in one shot. Fixed twin pairs: 6 (modern melancholy, rainy days) vs 11 (timeless hushed ballads), 1 (laid-back groove, cruising) vs 5 (euphoric party, pregame). Cluster 0 kept deliberately flat — no context vocab — so it only wins when nothing else matches.
- **Alpha bumped to 0.6**: eval confirmed 0.3 was fine numerically but in practice lyric sim was matching too literally (e.g. "alone" → songs with "alone" in lyrics regardless of feel). More audio weight makes results feel more like the mood rather than reading like the query.
- **Spotify availability check removed**: was calling Spotify search API per song to verify availability. Redundant now that `spotify_id` from the dataset is used directly for links — the ID is already valid.
- **Paging via /page endpoint**: full ranked pool of 50 cached under request_id for 30 min. Frontend can page through in slices of 10 without re-running SBERT routing or fusion. Images attached per page, not upfront.
- **Lazy year + image fetch**: Spotify GET /tracks/{id} called at query time for uncached songs only. Results stored in years_cache.json with {year, image} per song_id. 200ms sleep between calls, Retry-After on 429 saves cache and exits.
- **Spotify like/unlike endpoint**: `PUT/DELETE /v1/me/library?uris=spotify:track:{id}` — NOT `/v1/me/tracks` which returns 403 for dev-mode apps after Spotify's 2025 API restrictions.
- **Spotify OAuth token storage**: PostgreSQL `spotify_tokens` table via SQLAlchemy. Single-user app so `.first()` is used to retrieve the token. Upsert on re-login.
- **Auto-like after OAuth**: pending spotify_id stored in localStorage before redirect, fired on callback return via useEffect watching spotifyConnected.
- **LLM expansion trigger**: top-1 cosine < 0.45 OR top_cluster == 0. Threshold derived from routing score audit (melancholic=0.659, Sonic=0.388, drake=0.345, workout=0.307). Fires only on semantic_sbert path, not genre_lookup.
- **Expansion prompt**: 3-shot examples covering pop-culture (Sonic), artist-ref (SZA), and activity/context (bbq) failure modes. Output constrained to 5-8 comma-separated terms. Returns None on failure → falls back to original routing.
- **Cluster 0 band-aid deferred**: excluding cluster 0 on llm_expanded queries would work short-term but hardcodes a bad assumption. Real fix is rewriting cluster 0's description so it stops scoring broadly against unrelated queries (milestone 27).

## Stack
- **Backend**: FastAPI (Python), PostgreSQL + SQLAlchemy (OAuth token storage — live)
- **Frontend**: React (Vite)
- **ML pipeline**: lives in backend/ — numpy, pandas, SBERT, FAISS, scikit-learn

## Non-Goals
- Training a music-specific language model
- Production deployment
