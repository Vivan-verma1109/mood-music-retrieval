# Runs all 18 queries x 4 alpha values through the pipeline and writes ranked song IDs to rankings.jsonl (used by analyze_feedback.py).

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from backend.Stage4Fusion.fusion import query

QUERIES = [
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

ALPHAS = [0.0, 0.15, 0.3, 0.5]
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'rankings.jsonl')

if os.path.exists(OUTPUT_FILE):
    os.remove(OUTPUT_FILE)

for q in QUERIES:
    print(f"Query: {q}")
    for alpha in ALPHAS:
        results, _ = query(q, top_k=10, pop_candidates=50, alpha=alpha, check_spotify=False)
        rec = {
            "query": q,
            "alpha": alpha,
            "ranked_ids": [str(r['song_id']) for _, r in results.iterrows()],
        }
        with open(OUTPUT_FILE, 'a') as f:
            f.write(json.dumps(rec) + '\n')
    print(f"  done")

print(f"\nSaved to rankings.jsonl")
