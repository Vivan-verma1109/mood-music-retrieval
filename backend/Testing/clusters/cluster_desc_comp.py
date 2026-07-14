# Embeds all 13 cluster descriptions and prints a pairwise cosine similarity matrix, ranked pairs, and per-cluster nearest-neighbor gaps.
# Run as: python3 -m backend.Testing.cluter_desc_comp

import numpy as np 
from sentence_transformers import SentenceTransformer
from backend.config import cluster_descriptions, cluster_descriptions_old

model = SentenceTransformer("paraphrase-multilingual-mpnet-base-v2")
ids = sorted(cluster_descriptions.keys())
texts = []

for i in ids:
    texts.append(cluster_descriptions[i])

embs = model.encode(texts, normalize_embeddings = True)

# (13 x 768) x (768 x 13) - > 13 x 13
# [i][j] is dot of i and j, = costine sim cause unit vec
sim = embs @ embs.T 

print("    ", end="")
for i in ids:
    print(f"  {i:>3}", end="")
print()

for r in range(len(ids)):
    print(f"  {ids[r]:>2}", end="")
    for c in range(len(ids)):
        if ids[r] == ids[c]:
            print(f"     —", end="")
        else:
            print(f"  {sim[r][c]:.2f}", end="")
    print()

pairs = []
for r in range(len(ids)):
    for c in range( r + 1, len(ids)):
        pairs.append((ids[r], ids[c], sim[r][c]))

# sort by sim value
pairs.sort(key = lambda x: x[2], reverse = True)

print("\n=== Top pairs by similarity ===")
for i, j, val in pairs:
    print(f"  cluster {i} <-> cluster {j}: {val:.3f}")
    
print("\n=== Per-cluster nearest neighbor ===")
for r in range(len(ids)):
    row = []
    for c in range(len(ids)):
        if ids[r] != ids[c]:
            row.append((ids[c], sim[r][c]))
    row.sort(key=lambda x: x[1], reverse=True)
    nearest = row[0]
    second = row[1]
    gap = nearest[1] - second[1]
    print(f"  cluster {ids[r]}: nearest={nearest[0]} ({nearest[1]:.3f}), second={second[0]} ({second[1]:.3f}), gap={gap:.3f}")

old_texts = [cluster_descriptions_old[i] for i in ids]
old_embs = model.encode(old_texts, normalize_embeddings=True)
old_sim = old_embs @ old_embs.T

print("\n=== Twin pair similarity: old vs new ===")
for i, j in [(6, 11), (1, 5), (4, 7), (1, 8)]:
    o = old_sim[i][j]
    n = sim[i][j]
    print(f"  {i} vs {j}:  old={o:.4f}  new={n:.4f}  ({'DOWN' if n < o else 'UP'})")