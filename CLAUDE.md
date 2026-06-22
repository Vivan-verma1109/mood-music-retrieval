# Multimodal Mood-Based Music Retrieval

## Project Goal
Build a system that takes a natural language mood description ("I'm feeling melancholic and introspective")
and returns a ranked playlist by combining three signals:
1. **Acoustic features** — Spotify audio features (valence, energy, tempo, acousticness, danceability)
2. **Emotional clusters** — songs grouped by all 5 audio features (valence, energy, tempo, acousticness, danceability) into emotional neighborhoods
3. **Lyrics semantics** — SBERT embeddings of song lyrics aligned with the mood query

The core ML problems:
- Cluster songs into emotional neighborhoods (audio feature space)
- Map natural language mood descriptions into that same space
- Fuse audio cluster membership with lyric semantic similarity for final ranking

---

## Architecture

```
User mood query (text)
        ↓
   SBERT embedding
        ↓
  Projection layer ──→ audio feature space ──→ nearest emotional cluster
                                                        ↓
                                              candidate song pool
                                                        ↓
        ┌───────────────────────────────────────────────┤
        ↓                                               ↓
Audio feature similarity                   Lyric SBERT cosine similarity
(within cluster)                           (query vs. song lyrics)
        └───────────────────┬───────────────────────────┘
                            ↓
                   Weighted fusion score
                            ↓
                    Ranked playlist
```

## Pipeline Stages

### Stage 1 — Emotional Clustering
- Input: audio features (valence, energy, tempo, acousticness, danceability)
- Method: KMeans or HDBSCAN on normalized features
- Output: N clusters with human-readable mood labels (assigned manually or via centroid inspection)
- Why: constrains retrieval to emotionally coherent neighborhoods, reduces noise from full-corpus audio search

### Stage 2 — Lyric Embedding
- Input: lyrics text per song
- Method: paraphrase-multilingual-mpnet-base-v2 SBERT embeddings of all lyrics (run on GPU), build FAISS index
- Output: 955k × 768 embedding matrix + FAISS index for cosine similarity search
- Note: must run before Stage 3 — projection layer training uses these embeddings as input

### Stage 3 — Mood Query Projection
- Input: lyric SBERT embeddings (from Stage 2) + audio features per song
- Method: learned linear projection (768 → 5) trained on (SBERT(lyrics), audio_features) pairs
- Output: projection layer that maps any SBERT embedding → 5-dim audio space → nearest cluster
- Why lyrics not manual pairs: 955k training pairs vs ~50 manual ones, no domain mismatch risk

### Stage 4 — Fusion & Ranking
- Weighted combination: `score = α * audio_sim + (1-α) * lyric_sim`
- α is a tunable hyperparameter (start at 0.5, evaluate qualitatively)
- Instrumentals (no lyrics): lyric_sim = 0, fall back to audio score only (α = 1.0 for that song)
- Stretch: learn α via a small supervised layer if labeled mood→playlist data exists

---

## Data Requirements
- Audio features per track (valence, energy, tempo, acousticness, danceability, instrumentalness)
- Lyrics text per track
- Dataset TBD after inspecting available Kaggle options
- Target scale: 10k–50k songs

---

## Milestones
1. [ ] Dataset acquired and columns inspected
2. [ ] Audio features normalized, emotional clusters built and labeled
3. [ ] Lyrics embedded with bge-m3 on GPU, FAISS index built
4. [ ] Mood→audio projection trained on (SBERT(lyrics), audio_features) pairs
5. [ ] End-to-end query → cluster filter → lyric rerank working
6. [ ] Qualitative evaluation + fusion weight tuning
7. [ ] Demo interface (CLI or Gradio)
8. [ ] Music platform export — OAuth + create playlist from ranked results (Spotify Web API + Apple MusicKit)
9. [ ] (Stretch) Learned fusion weights

---

## Decisions & Rationale
- **SBERT over fine-tuned model**: fast, good zero-shot alignment, already familiar
- **Clustering before retrieval**: filters to emotional neighborhood first, prevents noisy full-corpus audio search
- **Two FAISS indices**: one for lyrics (SBERT), one optionally for audio — keeps modalities decoupled and fusion weight tunable
- **Not collaborative filtering**: no user interaction data; this is content-based + query-based only

## Non-Goals
- User accounts or personalization
- Training a music-specific language model
- Production deployment




  - valence — how happy/positive it sounds (0 to 1)
  - energy — intensity/power of the track (0 to 1)
  - tempo — BPM
  - acousticness — how acoustic vs. electronic (0 to 1)
  - danceability — how suitable for dancing (0 to 1)


All 5 features (valence, energy, tempo, acousticness, danceability) are used for clustering. The doc previously said valence+energy only — that was wrong. The implementation uses all 5 and the resulting cluster labels (Quiet/Acoustic Sadness, Moody Mid-Tempo, etc.) are better for it.

The clustering algorithm (KMeans or HDBSCAN) figures out the natural groupings from the data itself. You tell it how many
clusters you want (e.g. 8), it finds where songs naturally clump together in that space, and you label each cluster after 
the fact by inspecting what's in it.


SBERT converts text into a list of numbers (a vector) that captures meaning. We do this for every song's lyrics upfront, 
and also for your mood query at search time. Then we measure how similar the two vectors are — if your query and a song's 
lyrics are semantically close, that song scores high.


  - Clustering (valence/energy) — uses the audio feature numbers from the dataset
  - SBERT — uses the lyrics text from the dataset


  1. User input → SBERT → finds songs with matching lyrics
  2. User input → projection layer → maps into audio space → finds nearest cluster
  3. Both results get combined into one final score, score = α * audio_sim + (1-α) * lyric_sim
        You can tune it up or down depending on whether you want audio or lyrics to matter more.
        Skip lyric score — set lyric_sim to 0 and weight α to 1.0 (audio only) for that song


SBERT is used twice:
  1. Lyrics — SBERT embeds song lyrics (separate signal)
  2. Mood query — SBERT also embeds the user's input text, then the projection layer maps that embedding into audio space to find the nearest cluster

  projection layer is what connects SBERT to the clusters

  Projection layer = learned linear map from SBERT's 768-dim text vector → 5-dim audio feature space (like PCA but trained, not variance-based), so user input can be
  compared to clusters.

  Regarding the learned linear map We're making our own. You train it on pairs of (mood text, target audio features) — e.g. a song tagged "happy" should map close to the centroid of the
  high-valence/high-energy cluster. The training signal comes from mood tag labels in the dataset or manually labeled cluster centroids.

  Input text → SBERT embedding → projection layer → nearest cluster → candidate song pool → audio similarity + lyric similarity → weighted fusion → ranked playlist.