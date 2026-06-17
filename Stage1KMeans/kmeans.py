import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import MinMaxScaler # normalizes features to 0-1; fit finds min/max, transform applies (x - min) / (max - min)
from sklearn.cluster import KMeans

df = pd.read_csv("archive/songs_clean.csv")
print(df['id'].duplicated().sum())

#features = ['valence', 'energy', 'tempo', 'acousticness', 'danceability']
#scaler = MinMaxScaler()
X = np.load('archive/X_scaled.npy')
#np.save('archive/X_scaled.npy', X)

# (955307, 5) — 955k songs, 5 normalized features (0-1)
# [[0.193      0.605      0.40652907 0.00116466 0.41792548]
#  [0.287      0.648      0.32502336 0.90361446 0.79355488]
#  [0.         0.0354     0.         0.91164659 0.        ]]

kmeans = joblib.load('archive/kmeans_model.pkl')
df['cluster'] = kmeans.labels_ # assigns each song a cluster number 0-7
# print(df['cluster'].value_counts().sort_index())

# cluster
# 0     92883
# 1    155264
# 2    138576
# 3     92776
# 4     98370
# 5    143257
# 6     72727
# 7    161454
# Name: count, dtype: int64

# ------------------------------------------------------------------------------------------------------------------------------------------------ #

# print(df.groupby('cluster')[['valence', 'energy', 'tempo', 'acousticness', 'danceability']].mean().round(3))
#          valence  energy    tempo  acousticness  danceability
# cluster                                                      
# 0          0.229   0.243  110.672         0.851         0.425
# 1          0.577   0.866  134.102         0.046         0.500
# 2          0.353   0.591  116.989         0.106         0.624
# 3          0.299   0.488  118.445         0.475         0.503
# 4          0.760   0.675  121.664         0.493         0.652
# 5          0.229   0.878  130.378         0.023         0.372
# 6          0.606   0.384  116.850         0.780         0.607
# 7          0.788   0.738  119.652         0.104         0.709

# ------------------------------------------------------------------------------------------------------------------------------------------------ #

# KMeans always gets "better" (lower inertia) as you add more clusters — at some point adding more stops making a meaningful
# difference. The elbow is where that improvement flattens out. You pick the k at the bend. If the elbow is at 6, using 8 is
# not exactly effective

# inertias = []
# for k in range(4, 13): # 4 for lower bound happy/sad/energetic/calm), 13 upper cause beyond 12 clusters we have too many to label effectively
#    km = KMeans(n_clusters = k, random_state = 42, n_init = 10)
#    km.fit(X)
#    inertias.append((k, km.inertia_))
    
# for k, inertia in inertias:
#    print(f"k={k}: {inertia:.0f}")
    
# k=4: 95506
# k=5: 82947
# k=6: 76643
# k=7: 71558
# k=8: 67154
# k=9: 63444
# k=10: 60667
# k=11: 58562
# k=12: 56508

# ------------------------------------------------------------------------------------------------------------------------------------------------ #


# now for a silhouette score: it measures how well each point fits in its assigned 
# cluster versus how well it would fit in the next-nearest cluster.

# Random sample not full dataset — silhouette on 955k rows would take hours, 20k is fast and representative enough
# One sample not per-loop — we want the same 20k rows for every k so the scores are directly comparable. If each k got different rows
# the scores wouldn't be apples-to-apples

# from sklearn.metrics import silhouette_score

# np.random.seed(42) # tryna get consistent results to determine whether to use 4 or 5 clusters
# sample_idx = np.random.choice(len(X), 20000, replace=False)
# X_sample = X[sample_idx]

# for k in range(4, 10):
#    km = KMeans(n_clusters=k, random_state=42, n_init=10)
#    labels = km.fit_predict(X_sample)
#    score = silhouette_score(X_sample, labels)
#    print(f"k={k}: {score:.4f}")

# k=4: 0.2757
# k=5: 0.2751
# k=6: 0.2342
# k=7: 0.2228
# k=8: 0.2156
# k=9: 0.2108

# ------------------------------------------------------------------------------------------------------------------------------------------------ #

# print(df.groupby('cluster')[['valence', 'energy', 'acousticness', 'danceability']].mean().round(3))
#          valence  energy  acousticness  danceability
# cluster                                             
# 0          0.319   0.882         0.026         0.409
# 1          0.322   0.551         0.187         0.577
# 2          0.289   0.298         0.791         0.467
# 3          0.733   0.773         0.102         0.652
# 4          0.710   0.579         0.594         0.638

# ------------------------------------------------------------------------------------------------------------------------------------------------ #



cluster_labels = {
    0: 'Angry / Intense',
    1: 'Moody Mid-Tempo',
    2: 'Quiet / Acoustic Sadness',
    3: 'Euphoric / Party',
    4: 'Happy / Upbeat Acoustic'
}

df['mood'] = df['cluster'].map(cluster_labels)
df.to_csv('archive/songs_clustered.csv', index=False)
print(df[['name', 'artists', 'cluster', 'mood']].head(10))

#                             name         artists  cluster                      mood
# 0                              !        HELLYEAH        1          Moody Mid-Tempo
# 1                             !!         Yxngxr1        2  Quiet / Acoustic Sadness
# 2                !!! - Interlude          Glowie        2  Quiet / Acoustic Sadness
# 3                 !!De Repente!!         Rosendo        3          Euphoric / Party
# 4                 !!De Repente!!         Rosendo        3          Euphoric / Party
# 5            !!Noble Stabbings!!  Dillinger Four        0           Angry / Intense
# 6                 !I'll Be Back!           Rilès        3          Euphoric / Party
# 7                         !Lost!           Rilès        1          Moody Mid-Tempo
# 8      !Que Vida! - Mono Version            Love        4   Happy / Upbeat Acoustic
# 9  !Viva el Mal Viva el Capital!  Elektroduendes        3          Euphoric / Party
