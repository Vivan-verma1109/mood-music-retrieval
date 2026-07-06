# Last.fm integration — fetches listener counts and genre tags per artist to re-rank candidates.
# Caches results to artist_cache.json so repeated queries don't re-hit the API.
import json
import numpy as np
import requests
import os
from dotenv import load_dotenv

load_dotenv()
LASTFM_KEY = os.environ['LASTFM_API_KEY']

_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'artist_cache.json')

def _load_cache():
    try:
        with open(_CACHE_FILE) as f:
            return json.load(f)
    except:
        return {}

def _save_cache(cache):
    with open(_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

_artist_cache = _load_cache()


"""
Fetches listener count and artist tags from Last.fm using artist.getInfo.
Results are cached to backend/artist_cache.json so repeat artists skip the API call.

Args:
    artist (str): Artist name.
    track (str): Track name (unused in API call, kept for signature consistency).
Returns:
    tuple: (listeners: int, tags: list[str]) — tags are lowercase strings.
           Returns (0, []) on any failure.
"""
def get_track_info(artist, track):
    if artist in _artist_cache:
        return _artist_cache[artist]
    try:
        r = requests.get('https://ws.audioscrobbler.com/2.0/', params={
            'method': 'artist.getInfo',
            'api_key': LASTFM_KEY,
            'artist': artist,
            'format': 'json'
        }, timeout=3)
        data = r.json()['artist']
        listeners = int(data['stats']['listeners'])
        tags = [t['name'].lower() for t in data.get('tags', {}).get('tag', [])]
        _artist_cache[artist] = [listeners, tags]
        _save_cache(_artist_cache)
        return listeners, tags
    except:
        return 0, []

"""
Re-ranks candidate songs by combining lyric/audio scores with Last.fm listener counts.
Optionally boosts songs whose Last.fm tags match the requested genre (3x multiplier).
Songs with fewer than 100k listeners are filtered out.

Args:
    pool_idx (np.ndarray): DataFrame indices of candidate songs.
    pool_scores (np.ndarray): Fused lyric+audio scores for each candidate.
    df (DataFrame): Full songs DataFrame.
    top_k (int): Number of top songs to return.
    popularity_weight (float): How much listener count influences final score. Default 0.3.
    genre_song (list[str] | None): Last.fm tag aliases to boost 5x (from GENRE_ALIASES). None = no boost.
    genre_penalty (list[str] | None): Last.fm tag aliases to penalize 0.3x (all other genre aliases). None = no penalty.
Returns:
    tuple: (top_indices: np.ndarray, listeners: np.ndarray, final_scores: np.ndarray)
"""
def rerank_by_listeners(pool_idx, pool_scores, df, top_k, popularity_weight = 0.3, genre_song = None, genre_penalty = None):

    listeners = []
    tags = []
    for i in pool_idx:
        artist = df.loc[i, 'artists'].strip("[]'\"").split("'")[0]
        track = df.loc[i, 'name']
        popular, tag = get_track_info(artist, track)
        listeners.append(popular)
        tags.append(tag)
    listeners = np.array(listeners, dtype=float)

    median_l = np.median(listeners[listeners > 0]) if (listeners > 0).any() else 1
    listeners = np.where(listeners == 0, median_l, listeners)
    keep = listeners >= 10
    pool_idx = pool_idx[keep]
    pool_scores = pool_scores[keep]
    listeners = listeners[keep]
    tags = [tags[i] for i in np.where(keep)[0]]

    LISTENER_CAP = 10_000_000
    listeners_norm = np.minimum(listeners, LISTENER_CAP) / LISTENER_CAP

    final_score = pool_scores * (1 + popularity_weight * listeners_norm)
    genre_boost_fired = [False] * len(pool_idx)
    if genre_song or genre_penalty:
        for idx, tag in enumerate(tags):
            if genre_song and any(alias in tag for alias in genre_song):
                final_score[idx] *= 5
                genre_boost_fired[idx] = True
                print(f"  Genre boost: {df.loc[pool_idx[idx], 'name']}")
            elif genre_penalty and any(alias in tag for alias in genre_penalty):
                final_score[idx] *= 0.3
                print(f"  Genre penalty: {df.loc[pool_idx[idx], 'name']}")
    top_local = np.argsort(final_score)[::-1][:top_k]

    song_meta = [
        {
            "fused_score": float(pool_scores[i]),
            "listeners_norm": float(listeners_norm[i]),
            "genre_boost_fired": genre_boost_fired[i],
        }
        for i in top_local
    ]

    return pool_idx[top_local], listeners[top_local], final_score[top_local], song_meta
