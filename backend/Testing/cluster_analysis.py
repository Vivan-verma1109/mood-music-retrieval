# For each cluster: prints audio feature stats, top 20 artists by count, 25 nearest-centroid songs, and 25 random edge songs.
import pandas as pd
import numpy as np

FEATURES = ["valence", "energy", "tempo", "acousticness", "danceability", "speechiness", "instrumentalness"]
CSV = "backend/archive/songs_clustered.csv"

df = pd.read_csv(CSV)

# Normalize features for centroid distance (same scale as clustering)
df_feat = df[FEATURES].copy()
df_norm = (df_feat - df_feat.mean()) / df_feat.std()

for cluster_id in sorted(df["cluster"].unique()):
    mask = df["cluster"] == cluster_id
    cluster_df = df[mask].copy()
    cluster_norm = df_norm[mask].copy()

    print(f"\n{'='*60}")
    print(f"CLUSTER {cluster_id}  (n={len(cluster_df)})")
    print(f"{'='*60}")

    # Audio feature summary
    print("\n--- Audio Features (mean ± std) ---")
    for f in FEATURES:
        m = cluster_df[f].mean()
        s = cluster_df[f].std()
        print(f"  {f:20s}: {m:.3f} ± {s:.3f}")

    # Top 20 artists
    print("\n--- Top 20 Artists by Song Count ---")
    top_artists = cluster_df["artists"].value_counts().head(20)
    for artist, count in top_artists.items():
        print(f"  {count:5d}  {artist}")

    # 25 nearest centroid
    centroid = cluster_norm[FEATURES].mean()
    dists = np.sqrt(((cluster_norm[FEATURES] - centroid) ** 2).sum(axis=1))
    nearest_idx = dists.nsmallest(25).index
    print("\n--- 25 Nearest Centroid ---")
    for _, row in cluster_df.loc[nearest_idx, ["name", "artists"]].iterrows():
        print(f"  {row['name']}  —  {row['artists']}")

    # 25 random from the rest
    rest_idx = cluster_df.index.difference(nearest_idx)
    random_idx = cluster_df.loc[rest_idx].sample(min(25, len(rest_idx)), random_state=42).index
    print("\n--- 25 Random (edges) ---")
    for _, row in cluster_df.loc[random_idx, ["name", "artists"]].iterrows():
        print(f"  {row['name']}  —  {row['artists']}")

 