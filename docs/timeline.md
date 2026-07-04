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
- Embedded 845k song lyrics using paraphrase-multilingual-mpnet-base-v2 (multilingual, 768-dim)
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

## Stage 5 — Cluster Routing: Keyword Matching
- Introduced cluster_tags in config.py — keyword lists per cluster
- Query text scanned for keyword hits, top 2 clusters by hit count selected
- Problem: brittle — synonyms and paraphrases ("wistful", "nostalgic") missed entirely
- Fallback: lyric centroid cosine similarity if no keywords matched

## Stage 6 — Cluster Routing: Semantic SBERT (current)
- Replaced cluster_tags keyword lists with natural language cluster descriptionsadno
- Descriptions written based on audio centroid values + sampled song content per cluster
- At startup: descriptions encoded once with SBERT, stored as cluster_desc_embeddings (8×768)
- At query time: cosine sim between query embedding and cluster_desc_embeddings, top 2 selected
- Handles synonyms and paraphrases automatically
- Lyric centroid fallback dropped — semantic routing always returns a result
- **Decision: descriptions reflect audio characteristics, not just label names, since clusters are audio-feature neighborhoods**

## Stage 7 — Retraining with Expanded Feature Set (planned)
- Current clusters are noisy: rap mixed with rock in cluster 5, classical mixed with folk in cluster 0
- Root cause: speechiness and instrumentalness not included in original feature set
- speechiness separates rap/spoken word from singing
- instrumentalness separates vocal tracks from instrumentals
- Both features are in the dataset and computed from audio signal (independent of lyrics)
- **Decision: retrain KMeans with 7 features — valence, energy, tempo, acousticness, danceability, speechiness, instrumentalness**
- May revisit cluster count (currently 8) after seeing new centroid distributions
