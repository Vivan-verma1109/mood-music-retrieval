import numpy as np
import requests
import os
from dotenv import load_dotenv

load_dotenv()
LASTFM_KEY = os.environ['LASTFM_API_KEY']


"""
Fetches listener count and tags for a track from Last.fm.

Args:
    artist (str): Artist name.
    track (str): Track name.
Returns:
    tuple: (listeners: int, tags: list[dict]) — each tag dict has 'name' and 'url' keys.
            Returns (0, []) on any failure.
"""
def get_track_info(artist, track):

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
        return listeners, tags
    except:
        return 0, []

"""
Re-ranks candidate songs by boosting scores with Last.fm listener counts and optional genre match.

Args:
    pool_idx (np.ndarray): DataFrame indices of candidate songs.
    pool_scores (np.ndarray): Fused lyric+audio scores for each candidate.
    df (DataFrame): Full songs DataFrame.
    top_k (int): Number of top songs to return.
    popularity_weight (float): How much listener count influences final score. Default 0.5.
    genre_song (list[str] | None): Last.fm tag aliases to boost. None = no genre filtering.
Returns:
    tuple: (top_indices: np.ndarray, listeners: np.ndarray, final_scores: np.ndarray)
"""
def rerank_by_listeners(pool_idx, pool_scores, df, top_k, popularity_weight= 0.3, genre_song=None):

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
    LISTENER_CAP = 2_000_000
    listeners_norm = np.minimum(listeners, LISTENER_CAP) / LISTENER_CAP

    final_score = pool_scores * (1 + popularity_weight * listeners_norm)
    if genre_song:
        for idx, tag in enumerate(tags):
            tag_names = tag
            if any(alias in tag_names for alias in genre_song):
                final_score[idx] *= 1.8
                print(f"  Genre boost: {df.loc[pool_idx[idx], 'name']}")
    top_local = np.argsort(final_score)[::-1][:top_k]

    return pool_idx[top_local], listeners[top_local], final_score[top_local]
