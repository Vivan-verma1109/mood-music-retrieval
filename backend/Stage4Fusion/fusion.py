import numpy as np
from backend.config import cluster_tags, GENRE_ALIASES, GENRE_CLUSTERS
from backend.Stage4Fusion.loader import df, embeddings, X_scaled, model, cluster_ids, cluster_centroids, audio_centroids
from backend.Stage4Fusion.lastfm import rerank_by_listeners
from backend.Stage4Fusion.spotify import filter_available

"""
Scans query text for cluster keyword matches and returns the top 2 best-matching cluster IDs.

Args:
    mood_text (str): Raw user query.
Returns:
    list[int] | None: Top 2 cluster IDs sorted by hit count, or None if no keywords matched.
"""
def find_cluster_by_tags(mood_text):

    query_lower = mood_text.lower()
    hit_counts = {}
    for cluster_id, tags in cluster_tags.items():
        hits = sum(1 for tag in tags if tag in query_lower)
        if hits > 0:
            hit_counts[cluster_id] = hits
    if not hit_counts:
        return None
    sorted_clusters = sorted(hit_counts, key=hit_counts.get, reverse=True)
    return sorted_clusters[:2]

"""
Scans query text for genre keywords and returns the corresponding Last.fm tag aliases from GENRE_ALIASES.
Used as a fallback when no genre is passed explicitly from the UI.

Args:
    mood_text (str): Raw user query.
Returns:
    list[str] | None: Last.fm tag aliases for the best-matched genre, or None if no match.
"""
def find_genre_aliases(mood_text):

    query_lower = mood_text.lower()
    hit_counts = {}
    for cluster_id, tags in GENRE_ALIASES.items():
        hits = sum(1 for tag in tags if tag in query_lower)
        if hits > 0:
            hit_counts[cluster_id] = hits
    if not hit_counts:
        return None
    return GENRE_ALIASES[max(hit_counts, key=hit_counts.get)]

def cap_artists(pool_idx, pool_scores, df, max_per = 1):
    seen = {}
    keep = []
    for i, idx in enumerate(pool_idx):
        #normalize artist string 
        artist = df.loc[idx, 'artists'].lower().strip()
        count = seen.get(artist, 0)
        if count < max_per:
            seen[artist] = count + 1
            keep.append(i)
    keep = np.array(keep)
    return pool_idx[keep], pool_scores[keep]

"""
Full retrieval pipeline: embeds query, routes to emotional clusters, filters candidates,
scores by lyric + audio similarity, re-ranks by Last.fm listener count, and verifies Spotify availability.

Args:
    mood_text (str): Natural language mood description from the user.
    top_k (int): Number of songs to return. Default 10.
    pop_candidates (int): Candidate pool size passed to Last.fm re-ranking. Default 50.
    alpha (float): Weight for audio vs lyric similarity (0 = lyrics only, 1 = audio only). Default 0.3.
    language (str | None): ISO 639-1 language code to filter by (e.g. 'en'). None = no filter.
    genre (str | None): Genre key from GENRE_ALIASES (e.g. 'hiphop'). If None, auto-detected from query text.
    artist (str | None): Artist name to filter candidates to. None = no filter.
Returns:
    DataFrame: Ranked songs with columns name, artists, mood, valence, energy, listeners, score.
"""
def query(mood_text, top_k = 10, pop_candidates = 50, alpha = 0.3, language = None, genre = None, artist = None):

    # embed query
    query_emb = model.encode([mood_text], normalize_embeddings=True).astype('float32')

    if genre and genre in GENRE_CLUSTERS:
        cluster_ids_matched = GENRE_CLUSTERS[genre]
    else:
        cluster_ids_matched = find_cluster_by_tags(mood_text)
        if cluster_ids_matched is None:
            cluster_ids_matched = np.array(cluster_ids)[np.argsort((cluster_centroids @ query_emb.T).squeeze())[::-1][:2]].tolist()

    artists = [artist] if artist else None
    # resolve genre string to Last.fm tag aliases for the boost step
    genre_aliases = GENRE_ALIASES.get(genre) if genre else find_genre_aliases(mood_text)
    # collect all other genre aliases to penalize off-genre songs
    genre_penalty = [alias for key, aliases in GENRE_ALIASES.items() if key != genre for alias in aliases] if genre else None
    print(f"Nearest clusters: {cluster_ids_matched}")

    candidate_idx = df[df['cluster'].isin(cluster_ids_matched)].index.to_numpy()

    if language:
        lang_mask = df.loc[candidate_idx, 'language'] == language
        candidate_idx = candidate_idx[lang_mask.values]

    if artists:
        artist_lower = [a.lower() for a in artists]
        artist_col = df.loc[candidate_idx, 'artists'].fillna('').str.lower()
        artist_mask = artist_col.apply(lambda cell: any(a in cell for a in artist_lower))
        candidate_idx = candidate_idx[artist_mask.values]

    lyric_sim = (embeddings[candidate_idx] @ query_emb.T).squeeze()

    audio_centroid = np.mean([audio_centroids[c] for c in cluster_ids_matched], axis=0)
    audio_centroid /= np.linalg.norm(audio_centroid) + 1e-8

    candidate_audio = X_scaled[candidate_idx]
    candidate_audio_norm = candidate_audio / (np.linalg.norm(candidate_audio, axis=1, keepdims=True) + 1e-8)

    audio_sim = (candidate_audio_norm @ audio_centroid).squeeze()

    # fuse both signals — alpha controls audio vs lyric weight (0.3 = 30% audio, 70% lyrics)
    score = alpha * audio_sim + (1 - alpha) * lyric_sim

    # take top pool, re-rank by listener count
    top_pool = np.argsort(score)[::-1][:pop_candidates]
    pool_idx = candidate_idx[top_pool]
    pool_scores = score[top_pool]

    # cap each artist to 2 songs so the re-ranker sees variety
    pool_idx, pool_scores = cap_artists(pool_idx, pool_scores, df, max_per = 2)

    print(f"Fetching listener counts for top {pop_candidates} candidates...")
    top_global, listeners, final_scores = rerank_by_listeners(pool_idx, pool_scores, df, top_k=20, genre_song=genre_aliases, genre_penalty=genre_penalty)

    results = df.loc[top_global, ['name', 'artists', 'mood', 'valence', 'energy']].copy()
    results['listeners'] = listeners.astype(int)
    results['score'] = final_scores

    # dedup: strip parentheticals then match on artist + base title
    results['_name_lower'] = results['name'].str.lower().str.strip().str.replace(r'\s*[\(\[].*?[\)\]]', '', regex=True).str.strip()
    results['_artist_lower'] = results['artists'].str.lower().str.strip()
    results = results.drop_duplicates(subset=['_name_lower', '_artist_lower'])
    results = results.drop(columns=['_name_lower', '_artist_lower'])

    print("Verifying Spotify availability...")
    results = filter_available(results, top_k=top_k)
    return results


if __name__ == '__main__':
    query_text = "Something hindi like"
    print(f"\nQuery: {query_text}\n")
    results = query(query_text, top_k = 20, pop_candidates = 150)
    print(results.to_string(index=False))
