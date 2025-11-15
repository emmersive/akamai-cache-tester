"""Test the summary calculation"""

# Sample results with different cache statuses
test_results = [
    {'cache_hit': 'HIT'},
    {'cache_hit': 'HIT (inferred from timing)'},
    {'cache_hit': 'HIT (inferred from timing)'},
    {'cache_hit': 'MISS'},
    {'cache_hit': 'MISS (inferred from timing)'},
    {'cache_hit': 'REFRESH_HIT'},
    {'cache_hit': 'NOT_CACHEABLE'},
    {'cache_hit': 'ERROR'},
    {'cache_hit': 'UNKNOWN (timing inconclusive)'},
]

# Calculate statistics (same logic as in app.py)
total = len(test_results)

# Count hits (including inferred hits from timing)
hits = sum(1 for r in test_results if 'HIT' in r['cache_hit'])

# Count misses (including inferred misses from timing)
misses = sum(1 for r in test_results if 'MISS' in r['cache_hit'])

# Separate inferred vs confirmed for transparency
inferred_hits = sum(1 for r in test_results if r['cache_hit'] == 'HIT (inferred from timing)')
inferred_misses = sum(1 for r in test_results if r['cache_hit'] == 'MISS (inferred from timing)')
confirmed_hits = sum(1 for r in test_results if r['cache_hit'] in ['HIT', 'REFRESH_HIT'])
confirmed_misses = sum(1 for r in test_results if r['cache_hit'] in ['MISS', 'REFRESH_MISS'])

not_cacheable = sum(1 for r in test_results if r['cache_hit'] == 'NOT_CACHEABLE')
errors = sum(1 for r in test_results if r['cache_hit'] == 'ERROR')
unknown = sum(1 for r in test_results if 'UNKNOWN' in r['cache_hit'])

cacheable_total = total - not_cacheable - errors
cache_hit_ratio = (hits / cacheable_total * 100) if cacheable_total > 0 else 0

summary = {
    'total_urls': total,
    'cache_hits': hits,
    'cache_misses': misses,
    'confirmed_hits': confirmed_hits,
    'inferred_hits': inferred_hits,
    'confirmed_misses': confirmed_misses,
    'inferred_misses': inferred_misses,
    'not_cacheable': not_cacheable,
    'errors': errors,
    'unknown': unknown,
    'cache_hit_ratio': round(cache_hit_ratio, 2)
}

print("Test Results Summary:")
print("=" * 60)
for key, value in summary.items():
    print(f"{key:20s}: {value}")
print("=" * 60)
print(f"\nVerification:")
print(f"Total HITs (confirmed + inferred): {confirmed_hits} + {inferred_hits} = {hits}")
print(f"Total MISSes (confirmed + inferred): {confirmed_misses} + {inferred_misses} = {misses}")
print(f"Cache Hit Ratio: {hits}/{cacheable_total} = {cache_hit_ratio}%")
