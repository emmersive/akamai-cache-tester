# Akamai Cache Tester

A Python Flask web application that tests Akamai CDN cache performance by analyzing sitemap.xml files.

## Features

- 📊 **Sitemap Parsing**: Automatically extracts all URLs from sitemap.xml files (supports both regular sitemaps and sitemap indexes)
- 🔍 **Akamai Cache Testing**: Sends requests with Chrome user-agent and Akamai Pragma headers
- 📈 **Multi-Method Cache Detection**: Uses X-Cache headers, Age headers, and timing analysis to detect cache hits
- 🛡️ **Bot Protection Compatible**: Works even when debug headers are blocked by Akamai Bot Manager
- 📉 **Cache Hit Ratio**: Calculates overall cache performance metrics with detailed breakdowns
- 💾 **CSV Export**: Export detailed results including response times and all cache headers
- ⚡ **Concurrent Testing**: Tests multiple URLs simultaneously for faster results
- 🎨 **Modern UI**: Clean, responsive interface with real-time results

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

## Installation

1. **Create project directory**:
   ```bash
   mkdir akamai-cache-tester
   cd akamai-cache-tester
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Save the provided files**:
   - Save `app.py` in the project root
   - Save `requirements.txt` in the project root
   - Create `templates` directory: `mkdir templates`
   - Save `index.html` in the `templates` directory

4. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Start the Flask server**:
   ```bash
   python app.py
   ```

2. **Open your browser** and navigate to:
   ```
   http://localhost:5000
   ```

3. **Enter a sitemap URL** (e.g., `https://example.com/sitemap.xml`) and click "Test Sitemap"

4. **View results**:
   - Summary statistics showing cache hit ratio
   - Detailed table of all tested URLs
   - Cache status for each URL
   - Akamai headers (X-Cache, X-Check-Cacheable, etc.)

5. **Export results** to CSV for further analysis

## How It Works

### Akamai Pragma Headers

The application sends special Pragma headers with each request:
- `akamai-x-cache-on`: Returns X-Cache header with cache status
- `akamai-x-cache-remote-on`: Returns parent server cache information
- `akamai-x-check-cacheable`: Indicates if content is cacheable
- `akamai-x-get-cache-key`: Returns the cache key
- `akamai-x-get-true-cache-key`: Returns the true cache key

### Cache Status Types

The application identifies the following cache statuses:

- **HIT**: Content served from Akamai cache (TCP_HIT or TCP_MEM_HIT)
- **HIT (inferred from timing)**: Cache hit detected via response time analysis
- **MISS**: Content fetched from origin server (TCP_MISS)
- **MISS (inferred from timing)**: Cache miss detected via response time analysis
- **REFRESH_HIT**: Stale content refreshed and served from cache
- **REFRESH_MISS**: Stale content refreshed with new version from origin
- **NOT_CACHEABLE**: Content configured as non-cacheable
- **UNKNOWN (timing inconclusive)**: Response time between thresholds, cannot determine status
- **ERROR**: Request failed or timed out

### Cache Hit Detection Logic

The application uses a multi-method approach to detect cache hits, prioritized in the following order:

#### Method 1: X-Cache Header (Most Accurate)
When Akamai debug headers are enabled, the application checks the `X-Cache` header:
- `TCP_HIT` or `TCP_MEM_HIT` → **HIT**
- `TCP_MISS` → **MISS**
- `TCP_REFRESH_HIT` → **REFRESH_HIT**
- `TCP_REFRESH_MISS` → **REFRESH_MISS**
- `X-Check-Cacheable: NO` → **NOT_CACHEABLE**

#### Method 2: Age Header (Fallback)
If X-Cache is not available, checks the standard HTTP `Age` header:
- `Age: > 0` → **HIT** (content has been in cache for N seconds)

#### Method 3: X-Timer Analysis (Timing-Based Inference)
For sites that don't expose debug headers (common with bot protection), analyzes the `X-Timer` header:
- **Format**: `S<timestamp>,VS<varnish_hit>,VS<varnish_fetch>,VE<elapsed_ms>`
- **Logic**:
  - `VE < 100ms` → **HIT (inferred from timing)** - Fast response indicates cache
  - `VE > 500ms` → **MISS (inferred from timing)** - Slow response indicates origin fetch
  - `100ms ≤ VE ≤ 500ms` → **UNKNOWN (timing inconclusive)** - Ambiguous timing

**Example X-Timer values**:
```
X-Timer: S1763167085.909978,VS0,VS0,VE1        → 1ms = HIT
X-Timer: S1763167068.453172,VS0,VS0,VE16364   → 16,364ms = MISS
```

**Why Timing Works**:
- Cache hits retrieve content from edge servers (milliseconds)
- Cache misses require origin server roundtrip (hundreds of milliseconds or more)
- This method enables cache analysis even when debug headers are disabled or blocked by bot protection (e.g., Akamai Bot Manager)

### Cache Hit Ratio Calculation

```
Cache Hit Ratio = (Total Cache Hits / Total Cacheable URLs) × 100
```

Where:
- **Total Cache Hits** = Confirmed Hits + Inferred Hits (from timing analysis)
- **Total Cacheable URLs** = Total URLs - Not Cacheable - Errors

The calculation treats timing-inferred hits as positive cache hits, providing accurate cache performance metrics even when debug headers are unavailable.

#### Summary Statistics Breakdown

The summary includes both combined and detailed metrics:
- `cache_hits`: Total hits (confirmed + inferred)
- `cache_misses`: Total misses (confirmed + inferred)
- `confirmed_hits`: Hits verified via X-Cache headers
- `inferred_hits`: Hits detected via timing analysis
- `confirmed_misses`: Misses verified via X-Cache headers
- `inferred_misses`: Misses detected via timing analysis
- `not_cacheable`: URLs marked as non-cacheable
- `errors`: Request failures
- `unknown`: Timing inconclusive cases
- `cache_hit_ratio`: Percentage of cacheable URLs served from cache

## Project Structure

```
akamai-cache-tester/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── templates/
    └── index.html        # Web interface
```

## Configuration

### Modify Request Limits

In `app.py`, adjust the maximum URLs to test:

```python
max_urls = 100  # Change this value
```

### Adjust Concurrency

Modify the number of concurrent workers:

```python
with ThreadPoolExecutor(max_workers=10) as executor:  # Change max_workers
```

### Timeout Settings

Change request timeout (in seconds):

```python
response = requests.get(url, headers=headers, timeout=15)  # Adjust timeout
```

## Troubleshooting

### No Akamai Headers Returned

- Ensure the site is actually using Akamai CDN
- Some Akamai configurations may disable debug headers in production
- Check if the site blocks automated requests with bot protection

**Solution**: The tool will automatically fall back to timing-based analysis using the `X-Timer` header. Look for results showing `HIT (inferred from timing)` or `MISS (inferred from timing)`.

### Bot Protection / Request Timeouts

If you encounter timeouts or slow responses (especially with Akamai Bot Manager):
- The site may be using bot detection (cookies like `_abck`, `ak_bmsc`, `bm_sz`)
- Bot protection can delay or challenge automated requests
- Timing-based inference may show longer response times for first requests

**Solution**: The tool uses realistic browser headers and will still provide cache analysis via the X-Timer method. Initial requests may be slow, but subsequent requests from the same cache node should be fast.

### Sitemap Parse Errors

- Verify the sitemap URL is accessible
- Check if the sitemap follows the standard XML format (http://www.sitemaps.org/schemas/sitemap/0.9)
- Ensure sitemap is not blocked by robots.txt or authentication

### Slow Performance

- Reduce `max_workers` if you're hitting rate limits
- Increase timeout values for slow-responding sites (default: 15s per URL, 240s for sitemap)
- Test fewer URLs by reducing `max_urls`
- Consider that sites with bot protection may intentionally slow down automated requests

## Example Output

### Summary Statistics
```json
{
  "total_urls": 50,
  "cache_hits": 42,
  "cache_misses": 5,
  "confirmed_hits": 30,
  "inferred_hits": 12,
  "confirmed_misses": 3,
  "inferred_misses": 2,
  "not_cacheable": 2,
  "errors": 1,
  "unknown": 0,
  "cache_hit_ratio": 89.36
}
```

### CSV Export Columns
- URL
- Status Code
- Cache Status
- X-Cache
- X-Cache-Remote
- X-Check-Cacheable
- X-Cache-Key
- X-True-Cache-Key
- X-Served-By
- X-Timer
- Age
- Cache-Control
- Response Time (ms)
- Error (if any)

## Technical Details

### Dependencies

- **Flask**: Web framework
- **requests**: HTTP client for making HTTP requests
- **lxml**: XML parsing library
- **concurrent.futures**: Parallel request processing

### Browser User Agent

The application mimics Chrome browser:
```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36
```

## License

This project is provided as-is for testing and diagnostic purposes.

## Disclaimer

This tool is for diagnostic and testing purposes only. Always respect rate limits and terms of service when testing production sites.