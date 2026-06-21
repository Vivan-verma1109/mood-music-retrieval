import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import Ridge
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

df = pd.read_csv('archive/songs_clustered.csv')
embeddings = np.load('archive/lyrics_embeddings.npy')

# target: audio features each song was clustered on
features = ['valence', 'energy', 'tempo', 'acousticness', 'danceability']
X = embeddings            # (955307, 768) — lyric embeddings
y = df[features].values   # (955307, 5)   — audio features

# normalize targets to 0-1 (same scale kmeans was trained on)
scaler = MinMaxScaler()
y_scaled = scaler.fit_transform(y)

# hold out 10% for evaluation so we know the projection generalizes
X_train, X_test, y_train, y_test = train_test_split(X, y_scaled, test_size=0.1, random_state=42)

# linear projection: 768 -> 5
# alpha=1.0 penalizes large weights — safe default with 955k training pairs
proj = Ridge(alpha=1.0)
proj.fit(X_train, y_train)

joblib.dump(proj, 'archive/projection.pkl')
joblib.dump(scaler, 'archive/projection_scaler.pkl')
print("Projection layer trained and saved")

# R² per feature — how well lyric embeddings predict each audio dimension
y_pred = proj.predict(X_test)
for i, feat in enumerate(features):
    score = r2_score(y_test[:, i], y_pred[:, i])
    print(f"R² {feat}: {score:.4f}")

# sanity check: project a few embeddings and compare to actual cluster centroids
kmeans = joblib.load('archive/kmeans_model.pkl')
sample = embeddings[:5]
projected = proj.predict(sample)
print("\nProjected (first 5 songs):", projected)
print("Cluster centroids:", kmeans.cluster_centers_)
