# Analyzes year distribution of songs in years_cache.json.
# Two views: overall cache histogram, and per-query breakdown using two_pass_retrievals.jsonl.
# Run as: python -m backend.Testing.analysis.year_distributions

import json
from collections import defaultdict

CACHE_FILE = 'backend/Testing/data/years_cache.json'
RETRIEVALS_FILE = 'backend/Testing/data/two_pass_retrievals.jsonl'

buckets = {"pre-2000": 0, "2000-2005": 0, "2006-2011": 0, "2012-2017": 0, "2018-2023": 0, "2024+": 0, "unknown": 0}

with open(CACHE_FILE) as f:
    years_cache = json.load(f)
    for song, year in years_cache.items():
        if not year:
            buckets["unknown"] += 1
        elif year < 2000:
            buckets['pre-2000'] += 1
        elif 2000 <= year <= 2005:
            buckets["2000-2005"] += 1
        elif 2006 <= year <= 2011:
            buckets["2006-2011"] += 1
        elif 2012 <= year <= 2017:
            buckets["2012-2017"] += 1
        elif 2018 <= year <= 2023:
            buckets["2018-2023"] += 1
        elif year >= 2024:
            buckets["2024+"] += 1

for time, count in buckets.items():
    print(time, count)
