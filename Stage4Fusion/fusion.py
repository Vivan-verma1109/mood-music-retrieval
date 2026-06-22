import numpy as np
import pandas as pd
import faiss
import requests
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from config import cluster_tags

load_dotenv()
LASTFM_KEY = os.environ['LASTFM_API_KEY']

# --- load data ---
df = pd.read_csv('archive/songs_clustered.csv')
embeddings = np.load('archive/lyrics_embeddings.npy').astype('float32')
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

# --- cluster centroids in lyric space ---
cluster_ids = sorted(df['cluster'].unique())

centroids = []
# every song that belongs to cluster c, then pull their embeddings.
# Average those embeddings together and you get one vector that represents the "typical" lyric meaning of songs in that cluster. That's the centroid.
for c in cluster_ids:
    rows_in_cluster = df[df['cluster'] == c]        # get all rows in cluster c
    row_numbers = rows_in_cluster.index.to_numpy()  # get their row numbers as an array
    cluster_embeddings = embeddings[row_numbers]     # pull their 768-dim vectors from the matrix
    centroid = cluster_embeddings.mean(axis=0)       # average all those vectors into one 768-dim centroid
    centroids.append(centroid)

cluster_centroids = np.array(centroids).astype('float32')
cluster_centroids /= np.linalg.norm(cluster_centroids, axis=1, keepdims=True) + 1e-8  # normalize to length 1 so cosine sim works correctly

# popularity signal
def get_listeners(artist, track):
    try:
        r = requests.get('https://ws.audioscrobbler.com/2.0/', params={
            'method': 'track.getInfo',
            'api_key': LASTFM_KEY,
            'artist': artist,
            'track': track,
            'format': 'json'
        }, timeout=3)
        return int(r.json()['track']['listeners'])
    except:
        return 0

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

def query(mood_text, top_k = 10, pop_candidates = 50):

    # embed query
    query_emb = model.encode([mood_text], normalize_embeddings=True).astype('float32')

    # try tag matching first, fall back to lyric centroid routing
    cluster_id = find_cluster_by_tags(mood_text)
    if cluster_id is None:
        cluster_id = int(cluster_ids[np.argmax(cluster_centroids @ query_emb.T)])
    print(f"Nearest cluster: {cluster_id} — {df[df['cluster'] == cluster_id]['mood'].iloc[0]}")

    # score candidates by lyric cosine similarity
    candidate_idx = df[df['cluster'] == cluster_id].index.to_numpy()
    score = (embeddings[candidate_idx] @ query_emb.T).squeeze()

    # take top pool, re-rank by listener count
    top_pool = np.argsort(score)[::-1][:pop_candidates]
    pool_idx = candidate_idx[top_pool]
    pool_scores = score[top_pool]

    print(f"Fetching listener counts for top {pop_candidates} candidates...")
    listeners = np.array([
        get_listeners(df.loc[i, 'artists'].strip("[]'\"").split("'")[0], df.loc[i, 'name'])
        for i in pool_idx
    ], dtype=float)

    median_l = np.median(listeners[listeners > 0]) if (listeners > 0).any() else 1
    listeners = np.where(listeners == 0, median_l, listeners)
    listeners_norm = listeners / listeners.max()

    final_score = pool_scores * (1 + 0.5 * listeners_norm)
    top_local = np.argsort(final_score)[::-1][:top_k]
    top_global = pool_idx[top_local]

    results = df.loc[top_global, ['name', 'artists', 'mood', 'valence', 'energy']].copy()
    results['listeners'] = listeners[top_local].astype(int)
    results['score'] = final_score[top_local]
    return results


if __name__ == '__main__':
    query_text = "Im feeling Moody Mid-Tempo"
    print(f"\nQuery: {query_text}\n")
    results = query(query_text, top_k=10)
    print(results.to_string(index=False))
