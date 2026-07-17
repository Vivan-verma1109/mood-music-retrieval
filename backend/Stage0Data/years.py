# Year cache for candidate songs — fetches release year from Spotify GET /tracks/{id}.
# Owns the cache dict, fetch logic, and atomic writes to years_cache.json.
# years_cache is imported directly by fusion.py; no loader.py changes needed.

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()
_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
_token = None
_token_expiry = 0

_CACHE_FILE = os.path.join(os.path.dirname(__file__), '..', 'Testing', 'data', 'years_cache.json')

years_cache = {}

if os.path.exists(_CACHE_FILE):
    with open(_CACHE_FILE) as f:
        years_cache = json.load(f)
def _get_token():
    global _token, _token_expiry
    if _token and time.time() < _token_expiry - 60:
        return _token
    resp = requests.post(
        'https://accounts.spotify.com/api/token',
        data={'grant_type': 'client_credentials'},
        auth=(_CLIENT_ID, _CLIENT_SECRET),
    )
    resp.raise_for_status()
    data = resp.json()
    _token = data['access_token']
    _token_expiry = time.time() + data['expires_in']
    return _token


# Write to .tmp, then os.replace swaps atomically
def save_years_cache():
    tmp = _CACHE_FILE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(years_cache, f)
    os.replace(tmp, _CACHE_FILE)


                                                                                                                                                                                                                                                                                                                                              
def fetch_year(spotify_id):
    try:
        token = _get_token()
        resp = requests.get(
            f'https://api.spotify.com/v1/tracks/{spotify_id}',
            headers={'Authorization': f'Bearer {token}'},
            timeout=5,
        )
        if resp.status_code == 403:
            print(f"  [years] 403 — Spotify endpoint restricted")
            return None
        if resp.status_code == 429:
            wait = int(resp.headers.get('Retry-After', 5))
            print(f"  [years] rate limited {wait}s — saving checkpoint and stopping")
            save_years_cache()
            raise SystemExit(f"Rate limited for {wait}s. Resume later.")
        if resp.status_code != 200:
            print(f"  [years] {resp.status_code} — {spotify_id}")
            return None
        date = resp.json()['album']['release_date']
        year = int(date[:4]) if len(date) >= 4 else None
        print(f"  [years] {year} — {spotify_id}")
        time.sleep(0.2)  # 200ms between requests
        return year
    except Exception as e:
        print(f"  [years] error — {spotify_id}: {e}")
        return None