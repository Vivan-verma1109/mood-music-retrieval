import os
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials

load_dotenv()
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
    client_id=os.environ['SPOTIFY_CLIENT_ID'],
    client_secret=os.environ['SPOTIFY_CLIENT_SECRET']
))

def filter_available(results_df, top_k=10):
    verified = []
    for i, row in results_df.iterrows():
        
        search_query = f"track:{row['name']} artist:{row['artists']}"
        result = sp.search(q=search_query, type='track', limit=1)

        if result['tracks']['items']:
            verified.append(i)
        if len(verified) >= top_k:
            break
    return results_df.loc[verified]
