import numpy as np
from config import cluster_tags
from Stage4Fusion.loader import df, embeddings, X_scaled, model, cluster_ids, cluster_centroids, audio_centroids
from Stage4Fusion.lastfm import rerank_by_listeners
from Stage4Fusion.spotify import filter_available

def find_cluster_by_tags(mood_text):
    query_lower = mood_text.lower()
    hit_counts = {}
    for cluster_id, tags in cluster_tags.items():
        hits = sum(1 for tag in tags if tag in query_lower)
        if hits > 0:
            hit_counts[cluster_id] = hits
    if not hit_counts:
        return None
    return max(hit_counts, key=hit_counts.get)

def query(mood_text, top_k = 10, pop_candidates = 50, alpha = 0.3):

    # embed query
    query_emb = model.encode([mood_text], normalize_embeddings=True).astype('float32')

    # try tag matching first, fall back to lyric centroid routing
    cluster_id = find_cluster_by_tags(mood_text)
    if cluster_id is None:
        cluster_id = int(cluster_ids[np.argmax(cluster_centroids @ query_emb.T)])
    print(f"Nearest cluster: {cluster_id} — {df[df['cluster'] == cluster_id]['mood'].iloc[0]}")

    candidate_idx = df[df['cluster'] == cluster_id].index.to_numpy()

    # lyric cosine similarity
    lyric_sim = (embeddings[candidate_idx] @ query_emb.T).squeeze()

    # audio cosine similarity — how close each song's audio is to the matched cluster's centroid
    audio_centroid = audio_centroids[cluster_id]
    candidate_audio = X_scaled[candidate_idx]
    candidate_audio_norm = candidate_audio / (np.linalg.norm(candidate_audio, axis = 1, keepdims = True) + 1e-8)
    audio_sim = (candidate_audio_norm @ audio_centroid).squeeze()

    # fuse both signals — alpha controls audio vs lyric weight (0.3 = 30% audio, 70% lyrics)
    score = alpha * audio_sim + (1 - alpha) * lyric_sim

    # take top pool, re-rank by listener count
    top_pool = np.argsort(score)[::-1][:pop_candidates]
    pool_idx = candidate_idx[top_pool]
    pool_scores = score[top_pool]

    print(f"Fetching listener counts for top {pop_candidates} candidates...")
    top_global, listeners, final_scores = rerank_by_listeners(pool_idx, pool_scores, df, top_k=20)

    results = df.loc[top_global, ['name', 'artists', 'mood', 'valence', 'energy']].copy()
    results['listeners'] = listeners.astype(int)
    results['score'] = final_scores

    print("Verifying Spotify availability...")
    results = filter_available(results, top_k=top_k)
    return results


if __name__ == '__main__':
    query_text = "I'm feeling something fast like rap"
    print(f"\nQuery: {query_text}\n")
    results = query(query_text, top_k = 10)
    print(results.to_string(index=False))
