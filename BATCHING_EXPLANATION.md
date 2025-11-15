# Batch Processing Implementation

## Overview

The `/test` route has been reconfigured to process URLs in batches with delays between batches. This helps avoid overwhelming target servers and reduces the risk of rate limiting or triggering bot protection.

## Configuration

```python
batch_size = 10      # Process 10 URLs at a time
batch_delay = 1.0    # Wait 1 second between batches
max_workers = 10     # Maximum concurrent threads per batch
```

## How It Works

### Before (Original Implementation)
```
All 100 URLs → ThreadPoolExecutor (20 workers) → Process all at once
                                                    ↓
                                              All results returned
```

**Issues:**
- All URLs hit the server simultaneously
- Can trigger rate limiting
- Can trigger bot protection (Akamai Bot Manager)
- Puts heavy load on target server

### After (Batch Implementation)

```
URLs split into batches of 10:

Batch 1 (URLs 1-10)  → ThreadPoolExecutor (10 workers) → Results
        ↓
    Wait 1 second
        ↓
Batch 2 (URLs 11-20) → ThreadPoolExecutor (10 workers) → Results
        ↓
    Wait 1 second
        ↓
Batch 3 (URLs 21-30) → ThreadPoolExecutor (10 workers) → Results
        ↓
    ... and so on
```

**Benefits:**
- ✅ More respectful to target servers
- ✅ Less likely to trigger rate limiting
- ✅ Reduced bot detection risk
- ✅ Still processes URLs concurrently within each batch
- ✅ Predictable request rate

## Example Timing

For 100 URLs with batch_size=10 and batch_delay=1.0:

| Batch | URLs | Concurrent Workers | Delay After |
|-------|------|-------------------|-------------|
| 1 | 1-10 | 10 | 1 second |
| 2 | 11-20 | 10 | 1 second |
| 3 | 21-30 | 10 | 1 second |
| 4 | 31-40 | 10 | 1 second |
| 5 | 41-50 | 10 | 1 second |
| 6 | 51-60 | 10 | 1 second |
| 7 | 61-70 | 10 | 1 second |
| 8 | 71-80 | 10 | 1 second |
| 9 | 81-90 | 10 | 1 second |
| 10 | 91-100 | 10 | None (last batch) |

**Total batches:** 10
**Total delays:** 9 × 1 second = 9 seconds
**Request rate:** ~10 URLs per second (averaged)

## Code Implementation

```python
# Test URLs in batches to avoid overwhelming the server
batch_size = 10  # Process 10 URLs at a time
batch_delay = 1.0  # Wait 1 second between batches
results = []

# Split URLs into batches
for i in range(0, len(urls), batch_size):
    batch = urls[i:i + batch_size]

    # Process current batch concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_akamai_cache, url): url for url in batch}

        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)

    # Wait before processing next batch (unless this is the last batch)
    if i + batch_size < len(urls):
        time.sleep(batch_delay)
```

## Performance Characteristics

### Speed vs. Politeness Trade-off

| Approach | 100 URLs Completion Time | Server Load | Risk Level |
|----------|-------------------------|-------------|------------|
| Original (20 workers, no batching) | ~15-30 seconds | Very High | High |
| Batched (10 per batch, 1s delay) | ~24-39 seconds | Moderate | Low |
| Sequential (1 at a time) | ~250-500 seconds | Very Low | Very Low |

### Customization Options

You can adjust these values based on your needs:

```python
# More aggressive (faster, higher risk)
batch_size = 20
batch_delay = 0.5  # 500ms between batches
max_workers = 15

# More conservative (slower, safer)
batch_size = 5
batch_delay = 2.0  # 2 seconds between batches
max_workers = 5

# Very conservative (for strict rate limits)
batch_size = 3
batch_delay = 5.0  # 5 seconds between batches
max_workers = 3
```

## Verification

The batch processing has been tested and verified:

```bash
python3 test_batching.py
```

**Test Results:**
```
URLs processed: 25
Total time: 2.01 seconds
Expected minimum time: ~2 seconds (2 delays between 3 batches)
✅ Batch processing working correctly!
✅ Delays between batches confirmed
```

## Bot Protection Considerations

With Akamai Bot Manager or similar protection, the batched approach:

1. **Spreads out requests** over time (more human-like)
2. **Reduces simultaneous connections** (less suspicious)
3. **Allows cookies to be set** between batches (for bot detection)
4. **Gives server time to process** each batch before the next

### Example: Optus.com.au

For sites like Optus with Akamai Bot Manager:
- First request in batch may be slow (bot detection check)
- Subsequent requests in same batch will be faster
- Delay between batches allows bot manager to reset/cool down
- Overall more likely to complete successfully

## Impact on Results

✅ **No change to accuracy** - All URLs are still tested
✅ **No change to statistics** - Summary calculations unchanged
✅ **No change to features** - CSV export, headers, timing all work the same
⏱️ **Slightly longer completion time** - Trade-off for reliability

## Future Enhancements

Possible improvements:
1. Make `batch_size` and `batch_delay` configurable via request parameters
2. Adaptive batching based on response times
3. Exponential backoff if errors detected
4. Dynamic batch size based on server response headers
5. Progress streaming for long-running tests
