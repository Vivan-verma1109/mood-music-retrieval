import numpy as np
import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import MinMaxScaler

FEATURES = ['valence', 'energy', 'tempo', 'acousticness', 'danceability', 'speechiness', 'instrumentalness']

df = pd.read_csv('backend/archive/songs_clustered.csv')
X = df[FEATURES].values
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

np.save('backend/archive/X_scaled.npy', X_scaled)

kmeans = KMeans(n_clusters = 13, random_state = 42, n_init = 10)
kmeans.fit(X_scaled)

centroids = pd.DataFrame(kmeans.cluster_centers_, columns=FEATURES)
centroids.index.name = 'cluster'
print("\nCluster centroids:")
print(centroids.round(3).to_string())

df['cluster'] = kmeans.labels_
df.to_csv('backend/archive/songs_clustered.csv', index=False)
joblib.dump(kmeans, 'backend/archive/kmeans_model.pkl')
print("Saved.")

print("\nCluster sizes:")
print(pd.Series(kmeans.labels_).value_counts().sort_index())