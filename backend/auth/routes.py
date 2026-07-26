# the /auth/spotify and /auth/callback endpoints



from fastapi import APIRouter
from fastapi.responses import RedirectResponse
import requests
import os
import datetime
from backend.auth.db import SessionLocal
from backend.auth.models import SpotifyToken


router = APIRouter()

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
SPOTIFY_REDIRECT_URI = os.getenv('SPOTIFY_REDIRECT_URI')

# redirects the user to Spotify's login page
@router.get('/auth/spotify')
def spotify_login():
    params = '&'.join([
        'response_type=code',
        f'client_id={SPOTIFY_CLIENT_ID}',
        f'redirect_uri={SPOTIFY_REDIRECT_URI}',
        'scope=user-library-modify',
    ])
    return RedirectResponse(f'https://accounts.spotify.com/authorize?{params}')


# spotify calls this after login — exchanges code for tokens and saves to DB
@router.get('/auth/callback')
def spotify_callback(code: str):
    resp = requests.post('https://accounts.spotify.com/api/token', data={
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': SPOTIFY_REDIRECT_URI,
    }, auth=(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET))

    token_data = resp.json()
    print("token data:", token_data)
    expires_at = datetime.datetime.utcnow() + datetime.timedelta(seconds=token_data['expires_in'])

    # get users spotify id
    user_resp = requests.get('https://api.spotify.com/v1/me', headers={
          'Authorization': f'Bearer {token_data["access_token"]}'})

    user_json = user_resp.json()
    spotify_user_id = user_json['id']
    display_name = user_json.get('display_name', spotify_user_id)
    images = user_json.get('images', [])
    avatar = images[0]['url'] if images else ''

    # upsert

    db = SessionLocal()
    token = db.query(SpotifyToken).filter_by(spotify_user_id=spotify_user_id).first()
    if token:
        token.access_token = token_data['access_token']
        token.refresh_token = token_data['refresh_token']
        token.expires_at = expires_at
    else:
        token = SpotifyToken(
            spotify_user_id=spotify_user_id,
            access_token=token_data['access_token'],
            refresh_token=token_data['refresh_token'],
            expires_at=expires_at)
        db.add(token)
    db.commit()
    db.close()

    return RedirectResponse(f'http://localhost:5173?spotify=connected&spotify_user={display_name}&spotify_avatar={avatar}')
