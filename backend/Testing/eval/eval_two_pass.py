# Runs all 18 standard queries under both old and new cluster descriptions, records retrieval sets to two_pass_results.jsonl.
# Only surfaces songs never rated before for labeling. Results scored against full ratings store in analyze_feedback_descriptions.py.
# Run as: python -m backend.Testing.eval.eval_two_pass

import json
import time
import random
import os
from backend.config import cluster_descriptions_old
from backend.Stage4Fusion.fusion import query
from backend.Stage4Fusion.loader import model, df


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

ALPHA = 0.3
FEEDBACK_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'feedback.jsonl')
RETRIEVALS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'two_pass_retrievals.jsonl')
old_desc_embs = model.encode(
    [cluster_descriptions_old[i] for i in sorted(cluster_descriptions_old.keys())], normalize_embeddings = True).astype('float32')


def run_with_old():
    results = {}
    for mood_query in QUERIES:
        songs, _ = query(mood_query, top_k = 10, pop_candidates = 50, desc_embeddings = old_desc_embs, check_spotify = False)
        results[mood_query] = songs['song_id'].tolist()
    return results

def run_with_new():
    results = {}
    for mood_query in QUERIES:
        songs, _ = query(mood_query, top_k=10, pop_candidates=50, check_spotify=False)
        results[mood_query] = songs['song_id'].tolist()
    return results

old_results = run_with_old()
new_results = run_with_new()

# log full retrieval sets unconditionally so analysis can score all retrieved songs
with open(RETRIEVALS_FILE, 'w') as f:
    for mood_query in QUERIES:
        for sid in old_results[mood_query]:
            f.write(json.dumps({"query": mood_query, "song_id": sid, "desc_version": "old"}) + '\n')
        for sid in new_results[mood_query]:
            f.write(json.dumps({"query": mood_query, "song_id": sid, "desc_version": "new"}) + '\n')

seen = set()
if os.path.exists(FEEDBACK_FILE):
    with open(FEEDBACK_FILE) as f:
        for line in f:
            r = json.loads(line)
            seen.add((r['query'], str(r['song_id'])))
        
to_rate = []
for mood_query in QUERIES:
    for sid in old_results[mood_query]:
        if (mood_query, sid) not in seen:
            to_rate.append((mood_query, sid, 'old'))
    for sid in new_results[mood_query]:
        if (mood_query, sid) not in seen:
            to_rate.append((mood_query, sid, 'new'))
        
random.shuffle(to_rate)
print(f"\n{len(to_rate)} songs to rate. f=great  g=good  b=bad  t=terrible  s=skip  q=quit\n")
rating_map = {'f': 'great', 'g': 'good', 'b': 'bad', 't': 'terrible'}


for mood_query, sid, desc_version in to_rate:
    print(f"\n  [{mood_query}]")
    row = df.loc[int(sid)]
    print(f"  {row['name']} — {row['artists']}")
    rating = None
    while rating not in ('f', 'g', 'b', 't', 's', 'q'):
        rating = input("  > ").strip().lower()
    
    if rating == 'q':
        break
    if rating == 's':
        continue

    record = {
        "query": mood_query,
        "song_id": sid,
        "rating": rating_map[rating],
        "desc_version": desc_version,
        "alpha_at_rating": ALPHA,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    with open(FEEDBACK_FILE, 'a') as f:
        f.write(json.dumps(record) + '\n')