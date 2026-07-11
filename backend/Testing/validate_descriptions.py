import sys
import os
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from sentence_transformers import SentenceTransformer
from backend.config import cluster_descriptions

MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"

OLD_TWINS = {
    "6 vs 11 (old)": (
        "soft pop and soul ballads, emotional and warm, mid-tempo, romantic and heartfelt",
        "acoustic ballads and soft folk, intimate and gentle, classical vocals, quiet and beautiful",
    ),
    "1 vs 5 (old)": (
        "reggae, latin, and r&b grooves, warm and danceable, laid-back energy",
        "latin and world music, warm and celebratory, danceable and feel-good, reggae and tropical",
    ),
}

EVAL_QUERIES = [
    "sad songs for a rainy day",
    "songs to lift heavy to",
    "chill songs for driving at night",
    "music for when im in my feels",
    "happy songs to start the morning",
    "something drake like",
    "stuff that sounds like frank ocean",
    "sza type songs",
    "study music no lyrics",
    "songs for a summer bbq",
    "pregame playlist",
    "rnb slow jams",
    "sad indie acoustic",
    "hard trap beats",
    "90s hip hop vibes",
    "melancholic",
    "songs about heartbreak but upbeat",
    "spanish party music",
]

print(f"Loading {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)

# --- Baseline twin similarities (old descriptions) ---
print("\n=== Baseline twin similarities (old descriptions) ===")
baselines = {}
for name, (a, b) in OLD_TWINS.items():
    ea, eb = model.encode([a, b], normalize_embeddings=True)
    sim = float(np.dot(ea, eb))
    baselines[name] = sim
    print(f"  {name}: {sim:.4f}")

threshold = max(baselines.values())
print(f"\nFlag threshold (worst old twin): {threshold:.4f}")

# --- Embed new descriptions ---
descs = [cluster_descriptions[i] for i in range(13)]
embeddings = model.encode(descs, normalize_embeddings=True)
sim_matrix = embeddings @ embeddings.T

# --- Pairwise cosine matrix ---
print("\n=== Pairwise Cosine Similarity Matrix (new descriptions) ===")
print("     " + "".join(f"  {i:2d} " for i in range(13)))
for i in range(13):
    row = f"  {i:2d} "
    for j in range(13):
        if i == j:
            row += "  -- "
        else:
            v = sim_matrix[i][j]
            flag = "!" if v > threshold else " "
            row += f"{flag}{v:.2f}"
    print(row)

print("\nFlagged pairs (above old twin threshold):")
found = False
for i in range(13):
    for j in range(i + 1, 13):
        v = sim_matrix[i][j]
        if v > threshold:
            print(f"  Cluster {i} vs {j}: {v:.4f}")
            found = True
if not found:
    print("  None — all pairs below threshold.")

# --- Sanity routing ---
print("\n=== Sanity Routing — top 3 clusters per query ===")
EXPECTED = {
    "songs to lift heavy to": 4,
    "study music no lyrics": 9,
    "songs for a summer bbq": 8,
    "pregame playlist": 5,
    "melancholic": 6,
}
for q in EVAL_QUERIES:
    qe = model.encode(q, normalize_embeddings=True)
    sims = embeddings @ qe
    top3 = np.argsort(sims)[::-1][:3]
    expected = EXPECTED.get(q)
    winner = top3[0]
    flag = "" if expected is None else ("  OK" if winner == expected else f"  MISS (expected {expected})")
    print(f"\n  {q!r}{flag}")
    for rank, idx in enumerate(top3):
        margin = f"  (+{sims[idx] - sims[top3[1]]:.3f} over #2)" if rank == 0 else ""
        print(f"    {rank + 1}. Cluster {idx} [{sims[idx]:.4f}]{margin}  {cluster_descriptions[idx][:55]}...")
