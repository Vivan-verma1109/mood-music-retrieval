# Last.fm integration — fetches listener counts and genre tags per artist to re-rank candidates.
# Caches results to artist_cache.json so repeated queries don't re-hit the API.
import json
import numpy as np
import requests
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from backend.Stage0Data.years import years_cache




load_dotenv()
LASTFM_KEY = os.environ['LASTFM_API_KEY']

_CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'artist_cache.json')

# loads the artist cache from disk, returns empty dict if file doesn't exist
def _load_cache():
    try:
        with open(_CACHE_FILE) as f:
            return json.load(f)
    except:
        return {}

# writes the artist cache back to disk
def _save_cache(cache):
    with open(_CACHE_FILE, 'w') as f:
        json.dump(cache, f)

_artist_cache = _load_cache()
_cache_lock = threading.Lock()


# fetches listener count + genre tags from Last.fm for an artist, caches result so we don't re-hit the API
def get_track_info(artist, track):
    # check cache under lock to avoid duplicate fetches from parallel threads
    with _cache_lock:
        if artist in _artist_cache:
            return _artist_cache[artist]
    # fetch outside the lock so threads don't block each other on network calls
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
        result = [listeners, tags]
    except:
        result = [0, []]
    with _cache_lock:
        _artist_cache[artist] = result
    return result[0], result[1]

# re-ranks candidates by blending fused score with Last.fm listener count, applies genre boost/penalty
def rerank_by_listeners(pool_idx, pool_scores, df, top_k, popularity_weight = 0.3, genre_song = None, genre_penalty = None):

    # build (artist, track) pairs then fetch all in parallel
    pairs = [(df.loc[i, 'artists'].strip("[]'\"").split("'")[0], df.loc[i, 'name']) for i in pool_idx]
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(_fetch_one, pairs))
    _save_cache(_artist_cache)  # single write after all threads complete
    listeners = [r[0] for r in results]
    tags = [r[1] for r in results]

    listeners = np.array(listeners, dtype=float)

    median_l = np.median(listeners[listeners > 0]) if (listeners > 0).any() else 1
    listeners = np.where(listeners == 0, median_l, listeners)
    keep = listeners >= 50000
    pool_idx = pool_idx[keep]
    pool_scores = pool_scores[keep]
    listeners = listeners[keep]
    tags = [tags[i] for i in np.where(keep)[0]]

    LISTENER_CAP = 30_000_000
    listeners_norm = np.minimum(listeners, LISTENER_CAP) / LISTENER_CAP

    final_score = pool_scores * (1 + popularity_weight * listeners_norm)
    genre_boost_fired = [False] * len(pool_idx)
    if genre_song or genre_penalty:
        for idx, tag in enumerate(tags):
            if genre_song and any(alias in tag for alias in genre_song):
                final_score[idx] *= 2
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


# helper for parallel Last.fm fetches — takes (artist, track) tuple, returns (listeners, tags)
def _fetch_one(args):
    artist, track = args
    return get_track_info(artist, track)

# swaps the most-listened post-2000 song from the top 20 into slot 0 as a familiarity anchor
def pin_anchor(top_global, listeners, final_scores, song_meta):
    # sort top 20 by listeners desc, walk until we find one that isn't pre-2000
    top20_order = np.argsort(listeners[:20])[::-1]
    best = None
    for i in top20_order:
        info = years_cache.get(str(top_global[i]))
        year = info.get('year') if info else None
        if year is not None and year < 2000:
            continue
        best = int(i)
        break
    if best is None or best == 0:
        return top_global, listeners, final_scores, song_meta
    top_global[[0, best]] = top_global[[best, 0]]
    listeners[[0, best]] = listeners[[best, 0]]
    final_scores[[0, best]] = final_scores[[best, 0]]
    song_meta[0], song_meta[best] = song_meta[best], song_meta[0]
    return top_global, listeners, final_scores, song_meta
