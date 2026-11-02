# py-off-by-one

The loop misses the last window (should be `len(values) - window + 1`).

Expected: `app/stats.py:11` (bug).
