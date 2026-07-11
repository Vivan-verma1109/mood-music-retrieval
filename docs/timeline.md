# Project Timeline & Decision Log

## Stage 1 — Initial Clustering (5 clusters, audio features)
- Ran KMeans on 5 normalized audio features: valence, energy, tempo, acousticness, danceability
- Ran elbow analysis (k=4–12) and silhouette scoring (k=4–9)
- Silhouette peaked at k=4/5 statistically, but 5 felt too coarse for music retrieval
- **Decision: 5 clusters** — Angry/Intense, Moody Mid-Tempo, Quiet/Acoustic Sadness, Euphoric/Party, Happy/Upbeat Acoustic

## Stage 2 — Retraining to 8 Clusters (audio features)
- 5 clusters lacked granularity — couldn't distinguish e.g. chill acoustic from quiet sad, or dark R&B from moody mid-tempo
- **Decision: 8 clusters** — same 5 audio features, just more buckets
- New labels: Chill/Acoustic (0), Euphoric/Dance Pop (1), Angry/Intense (2), Moody Mid-Tempo (3), Happy/Upbeat Acoustic (4), High Energy/Hip-Hop (5), Quiet/Acoustic Sadness (6), Dark/Trap/R&B (7)
- Labels assigned manually after inspecting cluster centroids
- Note: lyric-based clustering ruled out — songs with no lyrics would have no embedding and be excluded from the dataset

## Stage 3 — Lyric Embeddings (SBERT)
- Embedded song lyrics using paraphrase-multilingual-mpnet-base-v2 (multilingual, 768-dim)
- Ran on GPU (RTX 5070, WSL2), ~28 min at batch size 128
- Tried bge-m3 first but it hung at batch 32
- Built FAISS IndexFlatIP for cosine similarity search
- **Decision: lyric embeddings used for scoring within clusters, not for routing**

## Stage 4 — Projection Layer (dropped)
- Trained Ridge regression 768→5 to project lyric embedding into audio feature space
- R²~0.2 across all features — too weak
- Caused wrong cluster routing: "melancholic" → Angry/Intense
- **Decision: dropped in favor of lyric centroid cosine similarity for cluster routing**
- File kept at archive/projection.pkl for future MLP experiments

## Stage 5 — Cluster Routing: Keyword Matching (dropped)
- Introduced cluster_tags in config.py — keyword lists per cluster
- Query text scanned for keyword hits, top 2 clusters by hit count selected
- Problem: brittle — synonyms and paraphrases ("wistful", "nostalgic") missed entirely
- Fallback: lyric centroid cosine similarity if no keywords matched

## Stage 6 — Cluster Routing: Semantic SBERT
- Replaced cluster_tags keyword lists with natural language cluster descriptions
- Descriptions written based on audio centroid values + sampled song content per cluster
- At startup: descriptions encoded once with SBERT, stored as cluster_desc_embeddings
- At query time: cosine sim between query embedding and cluster_desc_embeddings, top 2 selected
- Handles synonyms and paraphrases automatically
- Lyric centroid fallback dropped — semantic routing always returns a result
- **Decision: descriptions reflect audio characteristics, not just label names, since clusters are audio-feature neighborhoods**
- (Superseded in Stage 9: top 2 → top 3, and a second routing strategy added)

## Stage 7 — Retraining with Expanded Feature Set (done)
- Old clusters were noisy: rap mixed with rock in cluster 5, classical mixed with folk in cluster 0
- Root cause: speechiness and instrumentalness not in original feature set
- speechiness separates rap/spoken word from singing; instrumentalness separates vocal tracks from instrumentals
- **Decision: retrained KMeans with 7 features** — valence, energy, tempo, acousticness, danceability, speechiness, instrumentalness
- **Decision: 13 clusters** — cluster count revisited after seeing new centroid distributions
- New labels are genre-flavored: Hip-Hop/Rap, Dark Electronic, Metal/Hardcore, Jazz/Classical, Acoustic Ballads, Upbeat Pop, etc.
- Labels assigned manually from centroid values + 50-song samples per cluster

## Stage 8 — Deduplication
- Case-insensitive dedup on (song name, artist)
- Catalog reduced 955k → 845k songs
- FAISS index and embedding matrix filtered in sync to stay aligned with the deduped catalog

## Stage 9 — Cluster Routing: Two Strategies (current)
- **Strategy 1: UI genre selection** → direct GENRE_CLUSTERS lookup (deterministic, no embedding needed)
- **Strategy 2: free-text query** → SBERT cosine sim between query embedding and the 13 cluster description embeddings, top 3 selected
- **Decision: top 3, not top 2** — cluster 0 is a broad catch-all, so a wider net avoids starving niche queries
- Keyword matching fully dropped

## Stage 10 — Fusion & Reranking
- **Decision: alpha=0.3 audio+lyric blend** for candidate scoring
- Top 50 candidates reranked by Last.fm listener count: `final = lyric_score * (1 + 0.3 * listeners_norm)`
- Songs under 100k listeners filtered out
- 3x boost when Last.fm genre tags match the query genre
- Hard genre filter via track.getTopTags planned (boost → filter)

## Stage 11 — Eval System (current)
- Hand-labeled ~170 ratings across 18 queries at 4 alpha values (0, 0.15, 0.3, 0.5)
- Protocol: pooled, shuffled, blind rating (no alpha visible during labeling), scored with precision@10
- **Finding 1: alpha barely matters** — P@10 ranged 0.41–0.45 across the full sweep, top-10 lists mostly identical. Kept alpha=0.3, question closed.
- **Finding 2: routing quality explains nearly all variance** — mood-vocabulary queries hit 75–90% precision, context/activity queries hit 0–25%
- **Finding 3: audio_sim is flat (~0.96) across all rating levels** — the audio blend signal separates nothing within a pool
- Three failure classes taxonomized:
  1. Routing misses from vocabulary mismatch → fix: rewrite cluster descriptions
  2. Unsupported artist-in-free-text queries — artist names act as poison tokens → fix: artist detection (backlog)
  3. Hard constraint queries ("no lyrics") that embeddings can't honor → fix: instrumentalness threshold filter
- Root cause identified: cluster descriptions — clusters 6/11 and 1/5 are near-synonyms in embedding space, and none of the 13 descriptions contain activity/context vocabulary

## Remaining Milestones
- Rewrite cluster descriptions (separate 6/11 and 1/5, add activity/context vocabulary)
- Genre hard filter via track.getTopTags
- Instrumentalness threshold filter for "no lyrics" style queries
- Spotify OAuth + playlist export (PostgreSQL/SQLAlchemy)
- Liked songs filter, era filter