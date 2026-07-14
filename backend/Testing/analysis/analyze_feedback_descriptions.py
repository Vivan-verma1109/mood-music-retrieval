# Compares binary precision before vs after description rewrite, split by timestamp.
# Before = July 6-9 ratings at alpha=0.3. After = July 13 ratings.
# Run as: python -m backend.Testing.analysis.analyze_feedback_descriptions

import json
from collections import defaultdict

FEEDBACK_FILE = 'backend/Testing/data/feedback.jsonl'
CUTOFF = '2026-07-13T00:00:00Z'

before = defaultdict(list)
after = defaultdict(list)

with open(FEEDBACK_FILE) as f:
    for line in f:
        r = json.loads(line)
        if r.get('alpha_at_rating') != 0.3:
            continue
        score = 1 if r['rating'] in ('great', 'good') else 0
        q = r['query']
        if r['timestamp'] < CUTOFF:
            before[q].append(score)
        else:
            after[q].append(score)

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
