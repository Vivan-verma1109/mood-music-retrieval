import numpy as np
import pandas as pd
import joblib
import faiss
import requests
import os
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()
LASTFM_KEY = os.environ['LASTFM_API_KEY']

df = pd.read_csv('archive/songs_clustered.csv')
embeddings = np.load('archive/lyrics_embeddings.npy').astype('float32')
index = faiss.read_index('archive/lyrics_faiss.index')
scaler = joblib.load('archive/projection_scaler.pkl')
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

features = ['valence', 'energy', 'tempo', 'acousticness', 'danceability']

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
        data = r.json()
        return int(data['track']['listeners'])
    except:
        return 0

def query(mood_text, alpha=0.5, top_k=10, pop_candidates=50):
    query_emb = model.encode([mood_text], normalize_embeddings=True).astype('float32')

    centroid_sims = (cluster_centroids @ query_emb.T).squeeze()
    cluster_id = int(cluster_ids[np.argmax(centroid_sims)])
    print(f"Nearest cluster: {cluster_id} — {df[df['cluster'] == cluster_id]['mood'].iloc[0]}")

    candidate_idx = df[df['cluster'] == cluster_id].index.to_numpy()
    candidate_embs = embeddings[candidate_idx]
    lyric_sim = (candidate_embs @ query_emb.T).squeeze()
    audio_sim = lyric_sim

    instrumental_mask = df.loc[candidate_idx, 'instrumentalness'].values > 0.5
    effective_alpha = np.where(instrumental_mask, 1.0, alpha)
    score = effective_alpha * audio_sim + (1 - effective_alpha) * lyric_sim

    # take top pop_candidates, fetch listener counts, re-rank
    top_pool = np.argsort(score)[::-1][:pop_candidates]
    pool_idx = candidate_idx[top_pool]
    pool_scores = score[top_pool]

    print(f"Fetching listener counts for top {pop_candidates} candidates...")
    listeners = []
    for i in pool_idx:
        artist = df.loc[i, 'artists'].strip("[]'\"").split("'")[0]
        track = df.loc[i, 'name']
        listeners.append(get_listeners(artist, track))

    listeners = np.array(listeners, dtype=float)
    median_l = np.median(listeners[listeners > 0]) if (listeners > 0).any() else 1
    listeners = np.where(listeners == 0, median_l, listeners)
    max_l = listeners.max()
    listeners_norm = listeners / max_l

    final_score = pool_scores * (1 + 0.3 * listeners_norm)
    top_local = np.argsort(final_score)[::-1][:top_k]
    top_global = pool_idx[top_local]

    results = df.loc[top_global, ['name', 'artists', 'mood', 'valence', 'energy']].copy()
    results['listeners'] = listeners[top_local].astype(int)
    results['score'] = final_score[top_local]
    return results


if __name__ == '__main__':
    query_text = "I want something upbeat and energetic to start my morning"
    print(f"\nQuery: {query_text}\n")
    results = query(query_text, alpha=0.5, top_k=10)
    print(results.to_string(index=False))
