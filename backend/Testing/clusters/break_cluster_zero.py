# PCA scatter of cluster 0 to check if it's one blob or two separable groups
import numpy as np 
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from backend.Stage4Fusion.loader import df, X_scaled

mask = df['cluster'] == 0
X_c0 = X_scaled[mask.values]


# reduce 7 audio features down to 2 dimensions for plotting
pca = PCA(n_components=2)
X_2d = pca.fit_transform(X_c0)
print(f"Variance explained: PC1={pca.explained_variance_ratio_[0]:.1%}, PC2={pca.explained_variance_ratio_[1]:.1%}")


# scatter plot — sample 5k points so it doesn't take forever to render
sample_idx = np.random.choice(len(X_2d), size=min(5000, len(X_2d)), replace=False)
plt.figure(figsize=(8, 6))
plt.scatter(X_2d[sample_idx, 0], X_2d[sample_idx, 1], alpha=0.3, s=5, c='#1db954')
plt.title("Cluster 0 — PCA projection (7 audio features → 2D)")
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.tight_layout()
plt.savefig("backend/Testing/clusters/cluster0_pca.png", dpi=150)
print("saved to backend/Testing/clusters/cluster0_pca.png")