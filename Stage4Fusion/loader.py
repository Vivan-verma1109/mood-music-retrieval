import numpy as np
import pandas as pd
import joblib
from sentence_transformers import SentenceTransformer

df = pd.read_csv('archive/songs_clustered.csv')
embeddings = np.load('archive/lyrics_embeddings.npy').astype('float32')
X_scaled = np.load('archive/X_scaled.npy').astype('float32')
model = SentenceTransformer('paraphrase-multilingual-mpnet-base-v2')
kmeans = joblib.load('archive/kmeans_model.pkl')

# normalize KMeans audio centroids to unit length for cosine sim
audio_centroids = kmeans.cluster_centers_.astype('float32')
audio_centroids /= np.linalg.norm(audio_centroids, axis=1, keepdims=True) + 1e-8

# lyric-space cluster centroids — average embedding per cluster
cluster_ids = sorted(df['cluster'].unique())

centroids = []
# every song that belongs to cluster c, then pull their embeddings.
# Average those embeddings together and you get one vector that represents the "typical" lyric meaning of songs in that cluster. That's the centroid.
for c in cluster_ids:
    rows_in_cluster = df[df['cluster'] == c]        # get all rows in cluster c
    row_numbers = rows_in_cluster.index.to_numpy()  # get their row numbers as an array
    cluster_embeddings = embeddings[row_numbers]     # pull their 768-dim vectors from the matrix
    centroid = cluster_embeddings.mean(axis=0)       # average all those vectors into one 768-dim centroid
    centroids.append(centroid)

cluster_centroids = np.array(centroids).astype('float32')
cluster_centroids /= np.linalg.norm(cluster_centroids, axis=1, keepdims=True) + 1e-8  # normalize to length 1 so cosine sim works correctly
