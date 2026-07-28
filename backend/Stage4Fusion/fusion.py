# Core retrieval pipeline — takes a mood query and returns a ranked playlist.
# Handles cluster routing, candidate filtering, lyric+audio scoring, Last.fm re-ranking, and Spotify availability check.
import ast
import numpy as np
from backend.config import GENRE_ALIASES, GENRE_CLUSTERS
from backend.Stage4Fusion.loader import df, embeddings, X_scaled, model, cluster_ids, cluster_centroids, audio_centroids, cluster_desc_embeddings
from backend.Stage4Fusion.lastfm import rerank_by_listeners, pin_anchor
from backend.Stage0Data.years import years_cache, fetch_track_info, save_years_cache




# parses the artists column (stringified list) and checks if any artist exactly matches the input
def artist_matches(cell, artist_lower):
    try:
        names = [n.lower().strip() for n in ast.literal_eval(cell)]
        return any(a == n for a in artist_lower for n in names)
    except:
        return cell.lower().strip() in artist_lower


    
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
def query(mood_text, top_k = 10, pop_candidates = 100, alpha = 0.7, language = None, genre = None, artist = None, desc_embeddings = None):

    # embed query
    query_emb = model.encode([mood_text], normalize_embeddings=True).astype('float32')
    routing_strategy = ""

    if genre and genre in GENRE_CLUSTERS:
        cluster_ids_matched = GENRE_CLUSTERS[genre]
        routing_strategy = "genre_lookup"
    else:
        _desc_embeddings = desc_embeddings if desc_embeddings is not None else cluster_desc_embeddings
        sims = (_desc_embeddings @ query_emb.T).squeeze()
        top1_score = float(np.max(sims))
        top1_cluster = int(np.argmax(sims))

        if top1_score < 0.45 or top1_cluster == 0:
            from backend.Stage4Fusion.expand_query import expand_query
            expanded = expand_query(mood_text)
            if expanded:
                print(f"[expand] '{mood_text}' → '{expanded}'")
                expanded_emb = model.encode([expanded], normalize_embeddings=True).astype('float32')
                sims = (_desc_embeddings @ expanded_emb.T).squeeze()
                routing_strategy = "llm_expanded"
            else:
                routing_strategy = "semantic_sbert"
        else:
            routing_strategy = "semantic_sbert"

        cluster_ids_matched = np.array(cluster_ids)[np.argsort(sims)[::-1][:3]].tolist()

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
        artist_col = df.loc[candidate_idx, 'artists'].fillna('')
        artist_mask = artist_col.apply(lambda cell: artist_matches(cell, artist_lower))
        candidate_idx = candidate_idx[artist_mask.values]
        # if mood-matched clusters gave too few songs, fall back to all clusters
        if len(candidate_idx) < pop_candidates:
            all_idx = df[df['cluster'].isin(cluster_ids)].index.to_numpy()
            if language:
                lang_mask = df.loc[all_idx, 'language'] == language
                all_idx = all_idx[lang_mask.values]
            artist_col2 = df.loc[all_idx, 'artists'].fillna('')
            artist_mask2 = artist_col2.apply(lambda cell: artist_matches(cell, artist_lower))
            candidate_idx = all_idx[artist_mask2.values]
            routing_strategy = "artist_fallback"

    lyric_sim = (embeddings[candidate_idx] @ query_emb.T).reshape(-1)

    audio_centroid = np.mean([audio_centroids[c] for c in cluster_ids_matched], axis=0)
    audio_centroid /= np.linalg.norm(audio_centroid) + 1e-8

    candidate_audio = X_scaled[candidate_idx]
    candidate_audio_norm = candidate_audio / (np.linalg.norm(candidate_audio, axis=1, keepdims=True) + 1e-8)

    audio_sim = (candidate_audio_norm @ audio_centroid).reshape(-1)

    # fuse both signals — alpha controls audio vs lyric weight (0.3 = 30% audio, 70% lyrics)
    score = alpha * audio_sim + (1 - alpha) * lyric_sim

    sim_lookup = {
        int(candidate_idx[i]): (float(lyric_sim[i]), float(audio_sim[i]))
        for i in range(len(candidate_idx))
    }

    # take top pool, re-rank by listener count
    top_pool = np.argsort(score)[::-1][:pop_candidates]
    pool_idx = candidate_idx[top_pool]
    pool_scores = score[top_pool]

    # getting years for songs
    for idx in pool_idx:
        sid = str(idx)
        if sid not in years_cache:
            try:
                years_cache[sid] = fetch_track_info(df.loc[idx, 'id'])
                save_years_cache()
            except RuntimeError:
                break  # spotify rate limited — stop fetching years, continue with query
            except PermissionError:
                pass  # non-fatal, will retry next query

    print(f"Fetching listener counts for top {pop_candidates} candidates...")
    top_global, listeners, final_scores, song_meta = rerank_by_listeners(pool_idx, pool_scores, df, top_k=50, genre_song=genre_aliases, genre_penalty=genre_penalty)
    top_global, listeners, final_scores, song_meta = pin_anchor(top_global, listeners, final_scores, song_meta)  # pin most-listened to slot 0    

    results = df.loc[top_global, ['name', 'artists', 'mood', 'valence', 'energy', 'id']].copy()
    results['listeners'] = listeners.astype(int)
    results['score'] = final_scores

    # dedup: strip parentheticals then match on artist + base title
    results['_name_lower'] = results['name'].str.lower().str.strip().str.replace(r'\s*[\(\[].*?[\)\]]', '', regex=True).str.strip()
    results['_artist_lower'] = results['artists'].str.lower().str.strip()
    results = results.drop_duplicates(subset=['_name_lower', '_artist_lower'])
    results = results.drop(columns=['_name_lower', '_artist_lower'])
    results = results.rename(columns={'id': 'spotify_id'})
    results['song_id'] = results.index.astype(str)

    per_song = {}
    for rank_pos, (df_idx, meta) in enumerate(zip(top_global, song_meta)):
        song_id = str(df_idx)
        lyric_sim_val, audio_sim_val = sim_lookup.get(int(df_idx), (0.0, 0.0))
        per_song[song_id] = {
            "rank_position": rank_pos,
            "lyric_sim": lyric_sim_val,
            "audio_sim": audio_sim_val,
            "fused_score": meta["fused_score"],
            "listeners_norm": meta["listeners_norm"],
            "genre_boost_fired": meta["genre_boost_fired"],
            "final_score": float(final_scores[rank_pos]),
            "alpha_at_rating": alpha,
            "listener_weight": 0.3,
            "boost_multiplier": 5.0,
            "clusters": cluster_ids_matched,
            "routing_strategy": routing_strategy,
            "genre": genre,
            "query": mood_text,
        }

    return results, per_song


if __name__ == '__main__':
    query_text = "sad songs for a rainy day"
    print(f"\nQuery: {query_text}\n")
    results, _ = query(query_text, top_k = 50, pop_candidates = 50)
    print(results.to_string(index=False))
