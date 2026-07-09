import json
from collections import defaultdict

FEEDBACK_FILE = 'backend/Testing/feedback.jsonl'
RANKINGS_FILE = 'backend/Testing/rankings.jsonl'

SCORE = {'great': 1.0, 'good': 0.75, 'bad': 0.25, 'terrible': 0.0}

# load feedback — dedup by (query, song_id), keep latest timestamp
feedback = {}
with open(FEEDBACK_FILE) as f:
    for line in f:
        r = json.loads(line)
        key = (r['query'], r['song_id'])
        if key not in feedback or r['timestamp'] > feedback[key]['timestamp']:
            feedback[key] = r

# load rankings
rankings = []
with open(RANKINGS_FILE) as f:
    for line in f:
        rankings.append(json.loads(line))

# precision@10 per alpha per query
# only count songs that were actually rated
alpha_query_scores = defaultdict(lambda: defaultdict(list))

for entry in rankings:
    q = entry['query']
    alpha = entry['alpha']
    for rank, song_id in enumerate(entry['ranked_ids'][:10]):
        key = (q, song_id)
        if key in feedback:
            score = SCORE[feedback[key]['rating']]
            alpha_query_scores[alpha][q].append(score)

print("=== Precision@10 by alpha (avg score per rated song in top 10) ===\n")
alpha_totals = {}
for alpha in sorted(alpha_query_scores):
    query_avgs = []
    print(f"alpha={alpha}")
    for q, scores in sorted(alpha_query_scores[alpha].items()):
        avg = sum(scores) / len(scores)
        query_avgs.append(avg)
        print(f"  {q[:45]:<45} {avg:.2f}  ({len(scores)} rated)")
    overall = sum(query_avgs) / len(query_avgs) if query_avgs else 0
    alpha_totals[alpha] = overall
    print(f"  {'OVERALL':<45} {overall:.2f}\n")

print("=== Summary ===")
for alpha, score in sorted(alpha_totals.items(), key=lambda x: -x[1]):
    print(f"  alpha={alpha}: {score:.3f}")

print("\n=== Lyric sim vs audio sim by rating ===")
by_rating = defaultdict(lambda: {'lyric': [], 'audio': []})
with open(FEEDBACK_FILE) as f:
    for line in f:
        r = json.loads(line)
        by_rating[r['rating']]['lyric'].append(r['lyric_sim'])
        by_rating[r['rating']]['audio'].append(r['audio_sim'])

for rating in ['great', 'good', 'bad', 'terrible']:
    d = by_rating[rating]
    if not d['lyric']:
        continue
    avg_l = sum(d['lyric']) / len(d['lyric'])
    avg_a = sum(d['audio']) / len(d['audio'])
    print(f"  {rating:<10} lyric_sim={avg_l:.3f}  audio_sim={avg_a:.3f}  (n={len(d['lyric'])})")
