# Compares binary precision old vs new cluster descriptions using desc_version field.
# Only counts records written by eval_two_pass.py (those with desc_version = 'old' or 'new').
# Scores each retrieval set against all known ratings for that song+query.
# Run as: python -m backend.Testing.analysis.analyze_feedback_descriptions

import json
from collections import defaultdict

FEEDBACK_FILE = 'backend/Testing/data/feedback.jsonl'
RETRIEVALS_FILE = 'backend/Testing/data/two_pass_retrievals.jsonl'

# full ratings store — keyed by (query, song_id), all records
all_ratings = {}

with open(FEEDBACK_FILE) as f:
    for line in f:
        r = json.loads(line)
        if r.get('alpha_at_rating') != 0.3:
            continue
        key = (r['query'], str(r['song_id']))
        all_ratings[key] = 1 if r['rating'] in ('great', 'good') else 0

# retrieval sets from two_pass_retrievals.jsonl — full sets, not just newly-rated songs
old_songs = defaultdict(list)
new_songs = defaultdict(list)

with open(RETRIEVALS_FILE) as f:
    for line in f:
        r = json.loads(line)
        q = r['query']
        sid = str(r['song_id'])
        if r['desc_version'] == 'old':
            old_songs[q].append(sid)
        else:
            new_songs[q].append(sid)

# score each retrieval set against full ratings store
before = defaultdict(list)
after = defaultdict(list)

for q, sids in old_songs.items():
    for sid in sids:
        key = (q, sid)
        if key in all_ratings:
            before[q].append(all_ratings[key])

for q, sids in new_songs.items():
    for sid in sids:
        key = (q, sid)
        if key in all_ratings:
            after[q].append(all_ratings[key])

all_queries = sorted(set(before) | set(after))

print(f"  {'query':<45} {'before':>10} {'after':>10}")
print('-' * 70)

before_totals, after_totals = [], []
for q in all_queries:
    b = before[q]
    a = after[q]
    b_str = f"{sum(b)/len(b):.2f} ({len(b)})" if b else "—"
    a_str = f"{sum(a)/len(a):.2f} ({len(a)})" if a else "—"
    print(f"  {q[:43]:<43} {b_str:>12} {a_str:>12}")
    if b:
        before_totals.append(sum(b) / len(b))
    if a:
        after_totals.append(sum(a) / len(a))

print('-' * 70)
b_overall = f"{sum(before_totals)/len(before_totals):.2f}" if before_totals else "—"
a_overall = f"{sum(after_totals)/len(after_totals):.2f}" if after_totals else "—"
print(f"  {'OVERALL (per-query avg)':<43} {b_overall:>12} {a_overall:>12}")
