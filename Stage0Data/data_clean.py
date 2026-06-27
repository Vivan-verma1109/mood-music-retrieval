import pandas as pd

df = pd.read_csv('archive/songs_with_attributes_and_lyrics.csv')
#print(df.shape)
#print(df.columns.tolist())
#print(df.head(3))
#print(df.isnull().sum())

# (955320, 17) — 955k songs, 17 columns
# columns: id, name, album_name, artists, danceability, energy, key, loudness,
#          mode, speechiness, acousticness, instrumentalness, liveness,
#          valence, tempo, duration_ms, lyrics
# nulls: only 13 missing lyrics, 11 missing names, 570k missing album_name (unused)


df = df.dropna(subset = ['lyrics'])
df.to_csv('archive/songs_clean.csv', index=False)
print(df.shape)
# after dropping 13 rows with missing lyrics
# (955307, 17) — 955k songs ready for clustering