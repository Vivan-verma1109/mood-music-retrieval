import numpy as np
import requests
import os
from dotenv import load_dotenv

load_dotenv()
LASTFM_KEY = os.environ['LASTFM_API_KEY']

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

def rerank_by_listeners(pool_idx, pool_scores, df, top_k, popularity_weight = 0.5):
    listeners = []
    for i in pool_idx:
        artist = df.loc[i, 'artists'].strip("[]'\"").split("'")[0]
        track = df.loc[i, 'name']
        listeners.append(get_listeners(artist, track))
    listeners = np.array(listeners, dtype=float)

    median_l = np.median(listeners[listeners > 0]) if (listeners > 0).any() else 1
    listeners = np.where(listeners == 0, median_l, listeners)
    listeners_norm = listeners / listeners.max()

    final_score = pool_scores * (1 + popularity_weight * listeners_norm)
    top_local = np.argsort(final_score)[::-1][:top_k]

    return pool_idx[top_local], listeners[top_local], final_score[top_local]
