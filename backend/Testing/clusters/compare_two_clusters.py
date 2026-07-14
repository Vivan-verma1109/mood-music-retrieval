# Side-by-side cluster comparison: audio centroids + delta, top 5 artists, 50 nearest own centroid, 50 nearest other cluster's centroid. 
# Run as: python3 -m backend.Testing.compare_two_clusters <A> <B>

import numpy as np 
import pandas as pd 
import sys 
from backend.Stage4Fusion.loader import df, X_scaled

A = int(sys.argv[1])
B = int(sys.argv[2])

FEATURES = ["valence", "energy", "tempo", "acousticness", "danceability", "speechiness", "instrumentalness"]

mask_a = df['cluster'] == A
mask_b = df['cluster'] == B

df_a = df[mask_a].copy()
df_b = df[mask_b].copy()

X_a = X_scaled[mask_a]
X_b = X_scaled[mask_b]

centroid_a = X_a.mean(axis = 0)
centroid_b = X_b.mean(axis = 0)

print(f"\n{'='*60}")
print(f"CLUSTER {A} vs CLUSTER {B} — Audio Centroids")
print(f"{'='*60}")
print(f"{'feature':<20} {'cluster '+str(A):>10} {'cluster '+str(B):>10} {'delta':>10}")

for i, feat in enumerate(FEATURES):
    val_a = centroid_a[i]
    val_b = centroid_b[i]
    delta = val_a - val_b
    print(f"  {feat:<18} {val_a:>10.3f} {val_b:>10.3f} {delta:>10.3f}")


def print_top_artists(df_cluster, cluster_id):
    print(f"\n--- Cluster {cluster_id}: Top 5 Artists ---")
    total = len(df_cluster)
    top = df_cluster["artists"].value_counts().head(5)
    cumulative = 0
    for artist, count in top.items():
        pct = count / total * 100
        cumulative += pct
        print(f"  {count:>5}  {pct:>5.1f}%  {artist}")
    print(f"  top 5 covers {cumulative:.1f}% of cluster ({total} songs total)")
    
#  cumulative adds up the percentages of the top 5 artists. If top 5 artists cover 40% of the cluster, the cluster has a clear identity — a
#  handful of artists dominate it. If they only cover 5%, the cluster is spread thin across thousands of artists with no dominant sound.
#  That tells you how specific your description can be.

print_top_artists(df_a, A)
print_top_artists(df_b, B)


def print_nearest_centroid(df_cluster, X_cluster, centroid, cluster_id):
    dists = np.sqrt(((X_cluster - centroid) ** 2).sum(axis=1))
    nearest_idx = np.argsort(dists)[:50]
    print(f"\n--- Cluster {cluster_id}: 50 Nearest Own Centroid ---")
    for i in nearest_idx:
        row = df_cluster.iloc[i]
        print(f"  {row['name']}  —  {row['artists']}")
print_nearest_centroid(df_a, X_a, centroid_a, A)
print_nearest_centroid(df_b, X_b, centroid_b, B)
        
def print_boundary_songs(df_cluster, X_cluster, other_centroid, cluster_id, other_id):
    dists = np.sqrt(((X_cluster - other_centroid) ** 2).sum(axis=1))
    nearest_idx = np.argsort(dists)[:50]
    print(f"\n--- Cluster {cluster_id}: 50 Songs Nearest to Cluster {other_id}'s Centroid ---")
    for i in nearest_idx:
        row = df_cluster.iloc[i]
        print(f"  {row['name']}  —  {row['artists']}")

print_boundary_songs(df_a, X_a, centroid_b, A, B)
print_boundary_songs(df_b, X_b, centroid_a, B, A)