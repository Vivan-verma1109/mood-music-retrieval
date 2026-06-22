import numpy as np
import pandas as pd
import faiss
import requests
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
LASTFM_KEY = os.environ['LASTFM_API_KEY']

# --- load data ---
df = pd.read_csv('archive/songs_clustered.csv')
embeddings = np.load('archive/lyrics_embeddings.npy').astype('float32')
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

# --- cluster centroids in lyric space ---
cluster_ids = sorted(df['cluster'].unique())
cluster_centroids = np.array([
    embeddings[df[df['cluster'] == c].index.to_numpy()].mean(axis=0)
    for c in cluster_ids
]).astype('float32')
cluster_centroids /= np.linalg.norm(cluster_centroids, axis=1, keepdims=True) + 1e-8

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

def query(mood_text, top_k=10, pop_candidates=50):
    # embed query and find nearest cluster
    query_emb = model.encode([mood_text], normalize_embeddings=True).astype('float32')
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

    final_score = pool_scores * (1 + 0.3 * listeners_norm)
    top_local = np.argsort(final_score)[::-1][:top_k]
    top_global = pool_idx[top_local]

    results = df.loc[top_global, ['name', 'artists', 'mood', 'valence', 'energy']].copy()
    results['listeners'] = listeners[top_local].astype(int)
    results['score'] = final_score[top_local]
    return results


if __name__ == '__main__':
    query_text = "I'm feeling melancholic and introspective"
    print(f"\nQuery: {query_text}\n")
    results = query(query_text, top_k=10)
    print(results.to_string(index=False))
