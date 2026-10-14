# NOT USED IN CURRENT PIPELINE
# Trained Ridge regression (768 -> 5) to map SBERT embeddings into audio feature space.
# Dropped: R² ~0.2 caused wrong cluster routing ("melancholic" → Angry/Intense).
# Replaced by lyric-space centroid cosine similarity in fusion.py.
# Kept here for reference — revisit with MLP if projection is needed later.

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


#
# Projected (first 5 songs): 
# [[0.57243264 0.5894907  0.4875736  0.3049435  0.6304374 ]
# [0.48119685 0.7050117  0.51037467 0.1599997  0.58902717]
# [0.58246636 0.6863107  0.48709515 0.33226663 0.5352617 ]
# [0.57557184 0.67905056 0.5222948  0.33552605 0.59170943]
# [0.57557184 0.67905056 0.5222948  0.33552605 0.59170943]]


# Cluster centroids:
# [[0.31834384 0.88158994 0.53521369 0.02624341 0.41188698]
# [0.32282001 0.55132163 0.47843726 0.18737258 0.58193304]
# [0.28902274 0.29861373 0.4588708  0.79446589 0.47017999]
# [0.73303203 0.77351461 0.50331367 0.10270728 0.65654264]
# [0.71021773 0.5785708  0.48770265 0.59656975 0.64244961]]

# Projection layer trained and saved
# R² valence: 0.2134
# R² energy: 0.2033
# R² tempo: 0.0135
# R² acousticness: 0.1990
# R² danceability: 0.2494

#  Let's test the end-to-end pipeline first. If the results feel right qualitatively then 0.2 R² is fine in practice. If they feel off, we swap to MLP.
                                                                                                                                                                                                                                                   
#  No point optimizing blindly before we know if it's actually broken