import numpy as np
import pandas as pd
import joblib
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

# --- Config ---
K = 8
RUN_ANALYSIS = False  # set True to rerun elbow + silhouette (slow, ~10 min)
FEATURES = ['valence', 'energy', 'tempo', 'acousticness', 'danceability']

df = pd.read_csv('archive/songs_clustered.csv')
X = np.load('archive/X_scaled.npy')

# --- Elbow + silhouette (only runs if RUN_ANALYSIS = True) ---
if RUN_ANALYSIS:
    print("Elbow (inertia):")
    for k in range(4, 13):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        km.fit(X)
        print(f"  k={k}: {km.inertia_:.0f}")

    print("\nSilhouette (20k sample):")
    np.random.seed(42)
    idx = np.random.choice(len(X), 20_000, replace=False)
    X_s = X[idx]
    for k in range(4, 10):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        score = silhouette_score(X_s, km.fit_predict(X_s))
        print(f"  k={k}: {score:.4f}")

# --- Fit ---
print(f"Fitting KMeans k={K}...")
kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
kmeans.fit(X)

# --- Inspect centroids ---
centroids = pd.DataFrame(kmeans.cluster_centers_, columns=FEATURES)
centroids.index.name = 'cluster'
print("\nCluster centroids:")
print(centroids.round(3).to_string())
print("\nCluster sizes:")
print(pd.Series(kmeans.labels_).value_counts().sort_index())

# --- Label clusters (fill in after inspecting centroids above) ---
cluster_labels = {
    0: 'Chill / Acoustic',
    1: 'Euphoric / Dance Pop',
    2: 'Angry / Intense',
    3: 'Moody Mid-Tempo',
    4: 'Happy / Upbeat Acoustic',
    5: 'High Energy / Hip-Hop',
    6: 'Quiet / Acoustic Sadness',
    7: 'Dark / Trap / R&B',
}

# --- Save ---
df['cluster'] = kmeans.labels_
df['mood'] = df['cluster'].map(cluster_labels)
df.to_csv('archive/songs_clustered.csv', index=False)
joblib.dump(kmeans, 'archive/kmeans_model.pkl')
print("Saved songs_clustered.csv and kmeans_model.pkl")