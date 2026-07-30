# prints top-1 cluster routing score for a list of queries to help pick the LLM expansion threshold
# also compares old vs new cluster 0 description similarity to validate rewrites
import numpy as np
from backend.Stage4Fusion.loader import model, cluster_desc_embeddings, cluster_ids

OLD_CLUSTER_0 = "Mixed moody popular music. A broad blend of downcast pop, alternative, and atmospheric rock without one defining sound. Subdued and mid tempo. No specific activity or setting."

NEW_CLUSTER_0 = "Subdued mid-tempo produced pop and alternative. Emotionally muted — low-to-moderate valence, neither deeply sad nor euphoric. Mid energy, electric rather than acoustic, sung vocals. A mixed grab-bag of downcast pop, soft alternative, and atmospheric tracks that don't fit neatly into a single mood. Background listening for quiet or undefined emotional states."

queries = [
    "melancholic and rainy",
    "aggressive workout energy",
    "something drake like",
    "feels like Sonic the Hedgehog",
    "music for a bbq",
    "songs to lift heavy to",
    "late night chill",
]

old_emb = model.encode([OLD_CLUSTER_0], normalize_embeddings=True).astype('float32')
new_emb = model.encode([NEW_CLUSTER_0], normalize_embeddings=True).astype('float32')

print(f"\n{'Query':<35} {'old c0':>8} {'new c0':>8} {'delta':>8}")
print("-" * 62)
for q in queries:
    emb = model.encode([q], normalize_embeddings=True).astype('float32')
    old_score = float((old_emb @ emb.T).squeeze())
    new_score = float((new_emb @ emb.T).squeeze())
    print(f"{q:<35} {old_score:>8.3f} {new_score:>8.3f} {new_score - old_score:>+8.3f}")
