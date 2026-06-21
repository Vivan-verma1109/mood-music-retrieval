#  Stage 4 is fusion + ranking: the actual query pipeline. Here's what it does end-to-end:

#  1. User types a mood query
#  2. SBERT embeds it → projection layer → nearest cluster → candidate pool
#  3. FAISS searches lyric embeddings for semantic similarity
#  4. Final score = α * audio_sim + (1-α) * lyric_sim
#  5. Return top-k ranked songs

import numpy as np
import pandas as pd
import joblib
import faiss
from sentence_transformers import SentenceTransformer


# load everything we built in stages 1-3
df = pd.read_csv('archive/songs_clustered.csv')
embeddings = np.load('archive/lyrics_embeddings.npy').astype('float32')
index = faiss.read_index('archive/lyrics_faiss.index')
kmeans = joblib.load('archive/kmeans_model.pkl')
proj = joblib.load('archive/projection.pkl')
scaler = joblib.load('archive/projection_scaler.pkl')
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')

features = ['valence', 'energy', 'tempo', 'acousticness', 'danceability']