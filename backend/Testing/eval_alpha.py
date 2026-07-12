# Interactive blind rater: runs 18 queries across 4 alpha values, shuffles the pooled results, and records ratings to feedback.jsonl.
import json
import time
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from backend.Stage4Fusion.fusion import query

QUERIES = [
    # vibe/mood, phrased how people actually type
    "sad songs for a rainy day",
    "songs to lift heavy to",
    "chill songs for driving at night",
    "music for when im in my feels",
    "happy songs to start the morning",
    # artist-anchored (exercises artist bypass + "sounds like" semantics)
    "something drake like",
    "stuff that sounds like frank ocean",
    "sza type songs",
    # activity/context
    "study music no lyrics",
    "songs for a summer bbq",
    "pregame playlist",
    # genre-flavored (exercises genre lookup path)
    "rnb slow jams",
    "sad indie acoustic",
    "hard trap beats",
    "90s hip hop vibes",
    # curveballs / known weak spots
    "melancholic",              # the Ridge killer, keep it
    "songs about heartbreak but upbeat",   # cross-mood, tests top-3 routing
    "spanish party music",      # language filter path
]
ALPHAS = [0.0, 0.15, 0.3, 0.5]
FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), 'backend', 'feedback.jsonl')

def run():
    for mood_query in QUERIES:
        print(f"\n{'='*60}")
        print(f"Query: {mood_query}")
        print(f"{'='*60}")

        pooled = {}
        for alpha in ALPHAS:
            results, per_song = query(mood_query, top_k=10, pop_candidates=50, alpha=alpha)
            for _, row in results.iterrows():
                sid = row['song_id']
                if sid not in pooled:
                    pooled[sid] = (row, per_song.get(sid, {}))

        items = list(pooled.values())
        random.shuffle(items)

        print(f"\n{len(items)} songs to rate. f=great  g=good  b=bad  t=terrible  s=skip  q=next query\n")

        rating_map = {'f': 'great', 'g': 'good', 'b': 'bad', 't': 'terrible'}

        for row, meta in items:
            print(f"  {row['name']} — {row['artists']}")
            rating = None
            while rating not in ('f', 'g', 'b', 't', 's', 'q'):
                rating = input("  > ").strip().lower()

            if rating == 'q':
                break
            if rating == 's':
                continue

            record = {
                **meta,
                "song_id": row['song_id'],
                "rating": rating_map[rating],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            with open(FEEDBACK_FILE, 'a') as f:
                f.write(json.dumps(record) + '\n')

if __name__ == '__main__':
    run()
