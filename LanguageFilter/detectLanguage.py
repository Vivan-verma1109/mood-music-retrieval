import pandas as pd
from langdetect import detect

df = pd.read_csv('archive/songs_clustered.csv')

def detect_language(text):
    try:
        return detect(str(text))
    except:
        return 'unknown'

print(f'Detecting language for {len(df)} songs...')
# runs a function on every row in a column. So df['lyrics'].apply(detect_language) calls
# detect_language(text) once for each song's lyrics and returns a new column with the results.
df['language'] = df['lyrics'].apply(detect_language)
print("Done.")
print(df['language'].value_counts().head(20))
df.to_csv('archive/songs_clustered.csv', index=False)