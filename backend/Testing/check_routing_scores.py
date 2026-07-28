# prints top-1 cluster routing score for a list of queries to help pick the LLM expansion threshold
import numpy as np
from backend.Stage4Fusion.loader import model, cluster_desc_embeddings, cluster_ids

queries = [
    "melancholic and rainy",
    "aggressive workout energy",
    "something drake like",
    "feels like Sonic the Hedgehog",
    "music for a bbq",
    "songs to lift heavy to",
    "late night chill",
]

for q in queries:
    emb = model.encode([q], normalize_embeddings=True).astype('float32')
    sims = (cluster_desc_embeddings @ emb.T).squeeze()
    top1 = float(np.max(sims))
    top_cluster = int(np.argmax(sims))
    print(f"{top1:.3f}  cluster {top_cluster}  |  {q}")