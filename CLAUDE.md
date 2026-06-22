# Multimodal Mood-Based Music Retrieval

## Project Goal
Build a system that takes a natural language mood description ("I'm feeling melancholic and introspective")
and returns a ranked playlist by combining:
1. **Emotional clusters** — songs grouped by 5 audio features into emotional neighborhoods
2. **Lyrics semantics** — SBERT embeddings of song lyrics matched against the mood query
3. **Popularity signal** — Last.fm listener counts to surface recognizable songs

---

## Architecture

```
User mood query (text)
        ↓
   SBERT embedding
        ↓
  cosine sim vs. lyric-space cluster centroids ──→ nearest emotional cluster
                                                           ↓
                                                 candidate song pool (~170k songs)
                                                           ↓
                                          lyric cosine similarity (query vs. lyrics)
                                                           ↓
                                         top 50 → Last.fm listener count re-ranking
                                                           ↓
                                                   Ranked playlist
```

## Pipeline Stages

### Stage 1 — Emotional Clustering
- Input: audio features (valence, energy, tempo, acousticness, danceability)
- Method: KMeans (5 clusters) on normalized features
- Output: 5 clusters — Angry/Intense, Moody Mid-Tempo, Quiet/Acoustic Sadness, Euphoric/Party, Happy/Upbeat Acoustic
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
- Cluster routing: cosine sim between query embedding and per-cluster lyric centroids
- Candidate scoring: lyric cosine similarity (query vs. song embeddings)
- Re-ranking: top 50 candidates re-ranked with Last.fm listener count boost
  - `final_score = lyric_score * (1 + 0.3 * listeners_norm)`
  - Zero-listener songs get median listener count (neutral prior, not penalized)
- Audio similarity signal: pending — will use KMeans centroid cosine sim in audio space
- α fusion weight: dormant until audio_sim is properly implemented

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
- **Spotify Web API (Feb 2026)**: batch tracks endpoint (GET /tracks) removed, popularity field removed. Cannot use Spotify for popularity.
- **Last.fm API**: free, no OAuth for read calls. Used for listener counts via track.getInfo. Key in .env as LASTFM_API_KEY.

---

## Milestones
1. [x] Dataset acquired and columns inspected
2. [x] Audio features normalized, emotional clusters built and labeled (5 KMeans clusters)
3. [x] Lyrics embedded with SBERT on GPU, FAISS index built
4. [x] Projection layer trained (Ridge 768→5) — dropped in favor of lyric centroid routing
5. [x] End-to-end query → cluster filter → lyric rerank working
6. [ ] Restore audio similarity signal (KMeans centroid cosine sim in audio space)
7. [ ] Qualitative evaluation + fusion weight tuning
8. [ ] Genre filtering (Last.fm track.getTopTags)
9. [ ] Language filtering
10. [ ] Demo interface (Gradio)
11. [ ] Spotify playlist export (OAuth + POST /me/playlists)
12. [ ] Filter out user's liked songs from results
13. [ ] Release year / era filtering

---

## Decisions & Rationale
- **paraphrase-multilingual-mpnet-base-v2**: multilingual, 768-dim, fast at batch 128 on RTX 5070 (~28 min for 955k songs). bge-m3 tried first but hung at batch 32.
- **Lyric centroid routing over projection layer**: projection layer (R²~0.2) routed "melancholic" → Angry/Intense. Lyric centroid cosine sim routes correctly.
- **Last.fm over Spotify**: Spotify removed popularity field and batch tracks endpoint Feb 2026. Last.fm has listener counts, free, no quota issues.
- **Lazy Last.fm fetch**: only fetch for top 50 candidates per query. ~50 API calls, under 5 seconds.
- **Dedup on case-insensitive name+artist**: removed 110k duplicates. Embeddings and FAISS index filtered in sync.
- **Not collaborative filtering**: no user interaction data; content-based + query-based only.

## Non-Goals
- User accounts or personalization
- Training a music-specific language model
- Production deployment
