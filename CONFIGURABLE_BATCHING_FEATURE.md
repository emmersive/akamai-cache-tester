# Configurable Batch Processing Feature

## Summary

Added UI controls to make batch processing parameters configurable, allowing users to customize how URLs are processed during cache testing.

## Changes Made

### 1. Frontend Changes ([templates/index.html](templates/index.html))

#### Added Collapsible Configuration Section

**Configuration Toggle Button:**
The three new input fields are grouped in a collapsible "Configuration" section that is hidden by default. Users can click the toggle button to show/hide the configuration options.

```html
<div class="config-toggle" onclick="toggleConfiguration()">
    <div class="config-toggle-text">
        <span>⚙️ Configuration</span>
        <span style="font-size: 12px; color: #6c757d; font-weight: normal;">(Batch size, delays, limits)</span>
    </div>
    <span class="config-toggle-icon" id="configToggleIcon">▼</span>
</div>
```

#### Added 3 New Input Fields (Lines 432-463)

**Batch Size Input:**
```html
<div class="input-group">
    <label for="batchSize">Batch Size</label>
    <input
        type="number"
        id="batchSize"
        placeholder="3"
        value="3"
        min="1"
        max="100">
</div>
```

**Batch Delay Input:**
```html
<div class="input-group">
    <label for="batchDelay">Pause Between Batches (seconds)</label>
    <input
        type="number"
        id="batchDelay"
        placeholder="1.0"
        value="1.0"
        min="0"
        max="10"
        step="0.1">
</div>
```

**Max URLs Input:**
```html
<div class="input-group">
    <label for="maxUrls">Max URLs (optional)</label>
    <input
        type="number"
        id="maxUrls"
        placeholder="No limit"
        value=""
        min="1">
</div>
```

#### Updated JavaScript `runTest()` Function (Lines 480-529)

**Added parameter reading:**
```javascript
const batchSize = parseInt(document.getElementById('batchSize').value) || 3;
const batchDelay = parseFloat(document.getElementById('batchDelay').value) || 1.0;
const maxUrlsValue = document.getElementById('maxUrls').value.trim();
const maxUrls = maxUrlsValue ? parseInt(maxUrlsValue) : null;
```

**Added client-side validation:**
```javascript
// Validate batch size and delay
if (batchSize < 1 || batchSize > 100) {
    showError('Batch size must be between 1 and 100');
    return;
}

if (batchDelay < 0 || batchDelay > 10) {
    showError('Batch delay must be between 0 and 10 seconds');
    return;
}

if (maxUrls !== null && maxUrls < 1) {
    showError('Max URLs must be at least 1');
    return;
}
```

**Updated request body:**
```javascript
body: JSON.stringify({
    sitemap_url: sitemapUrl,
    check_aem: checkAem,
    batch_size: batchSize,
    batch_delay: batchDelay,
    max_urls: maxUrls
})
```

### 2. Backend Changes ([app.py](app.py))

#### Updated `/test` Endpoint (Lines 340-402)

**Added new parameters to docstring:**
```python
Request JSON parameters:
- sitemap_url (str): URL of the sitemap to test
- check_aem (bool, optional): Whether to check for AEM detection (default: True)
- batch_size (int, optional): Number of URLs to process per batch (default: 3)
- batch_delay (float, optional): Seconds to wait between batches (default: 1.0)
- max_urls (int, optional): Maximum number of URLs to process (default: None/unlimited)
```

**Read parameters from request:**
```python
batch_size = data.get('batch_size', URL_BATCH_SIZE)  # Default to constant
batch_delay = data.get('batch_delay', BATCH_DELAY)  # Default to constant
max_urls = data.get('max_urls', None)  # Default to None (no limit)
```

**Added server-side validation:**
```python
if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 100:
    return jsonify({'error': 'Batch size must be an integer between 1 and 100'}), 400

if not isinstance(batch_delay, (int, float)) or batch_delay < 0 or batch_delay > 10:
    return jsonify({'error': 'Batch delay must be a number between 0 and 10'}), 400

if max_urls is not None and (not isinstance(max_urls, int) or max_urls < 1):
    return jsonify({'error': 'Max URLs must be a positive integer'}), 400
```

**Apply max_urls limit:**
```python
# Apply max_urls limit if specified
if max_urls is not None and len(urls) > max_urls:
    urls = urls[:max_urls]
```

**Use parameters in batch processing:**
```python
# Split URLs into batches
for i in range(0, len(urls), batch_size):
    batch = urls[i:i + batch_size]

    # Process current batch concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_url = {executor.submit(check_akamai_cache, url, check_aem): url for url in batch}

        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)

    # Wait before processing next batch (unless this is the last batch)
    if i + batch_size < len(urls):
        time.sleep(batch_delay)
```

### 3. Tests ([test_configurable_batching.py](test_configurable_batching.py))

Created comprehensive unit tests with 6 test cases:

| Test | Purpose |
|------|---------|
| `test_default_batch_parameters` | Verifies defaults are used when parameters not provided |
| `test_custom_batch_size` | Verifies custom batch size is applied |
| `test_max_urls_limit` | Verifies max_urls limit works correctly |
| `test_invalid_batch_size` | Verifies validation rejects invalid batch size |
| `test_invalid_batch_delay` | Verifies validation rejects invalid batch delay |
| `test_invalid_max_urls` | Verifies validation rejects invalid max_urls |

**All tests pass:**
```
Ran 6 tests in 2.025s
OK
```

## Usage

### UI Configuration

**Collapsible Configuration Section:**
The configuration options are grouped in a collapsible section that is hidden by default. Click the "⚙️ Configuration" button to expand or collapse the section. This keeps the UI clean for users who want to use default settings.

**Default Values:**
- Batch Size: 3 URLs per batch
- Pause Between Batches: 1.0 seconds
- Max URLs: No limit (empty field)

**Validation Ranges:**
- Batch Size: 1-100
- Pause Between Batches: 0-10 seconds
- Max URLs: 1+ (optional)

**UI Features:**
- Configuration section collapsed by default
- Click toggle button to show/hide configuration
- Smooth animation when expanding/collapsing
- Visual indicator (▼/▲) shows current state
- Settings are preserved when collapsed

### Use Cases

#### Use Case 1: Test Small Batches with Longer Delays
```
Batch Size: 2
Pause: 3.0 seconds
Max URLs: (empty)
```
**Result**: Processes 2 URLs at a time, waits 3 seconds between batches, processes all URLs from sitemap

#### Use Case 2: Fast Testing with No Delays
```
Batch Size: 20
Pause: 0
Max URLs: (empty)
```
**Result**: Processes 20 URLs at a time with no delays (fastest possible)

#### Use Case 3: Quick Sample Test
```
Batch Size: 5
Pause: 1.0
Max URLs: 10
```
**Result**: Tests only first 10 URLs from sitemap, 5 at a time with 1 second delay

#### Use Case 4: Aggressive Bot Protection Sites
```
Batch Size: 1
Pause: 5.0
Max URLs: (empty)
```
**Result**: Processes 1 URL at a time, waits 5 seconds between each (most conservative)

### API Request Format

**With all parameters:**
```json
{
  "sitemap_url": "https://example.com/sitemap.xml",
  "check_aem": true,
  "batch_size": 5,
  "batch_delay": 2.0,
  "max_urls": 50
}
```

**With defaults (backward compatible):**
```json
{
  "sitemap_url": "https://example.com/sitemap.xml"
}
```

## Benefits

### 1. Flexibility
- Users can adjust batch processing to match their needs
- Can handle both aggressive bot protection and performance optimization

### 2. Rate Limiting Control
- Fine-tune request rates to avoid triggering bot protection
- Adjust based on target site's tolerance

### 3. Quick Testing
- Use max_urls for quick sample tests
- No need to wait for entire sitemap processing

### 4. Performance Optimization
- Increase batch size and reduce delays for fast, unrestricted sites
- Maximize throughput when possible

### 5. Backward Compatibility
- All parameters are optional
- Existing API calls work without modification
- Default values match previous hardcoded constants

## Technical Details

### Parameter Defaults

The hardcoded constants are still used as fallback defaults:

```python
# app.py lines 41-43
URL_BATCH_SIZE = 3  # Process 10 URLs at a time
BATCH_DELAY = 1.0  # Wait 1 second between batches
```

When parameters are not provided in the request, these constants are used:
```python
batch_size = data.get('batch_size', URL_BATCH_SIZE)
batch_delay = data.get('batch_delay', BATCH_DELAY)
```

### Validation Strategy

**Client-Side Validation:**
- Immediate feedback to user
- Prevents invalid requests
- Better UX with instant error messages

**Server-Side Validation:**
- Security layer (never trust client)
- Type checking (int, float, None)
- Range validation
- Returns 400 Bad Request with error message

### Max URLs Implementation

Unlike batch_size and batch_delay which always have values, max_urls can be `None`:

```python
max_urls = data.get('max_urls', None)

if max_urls is not None and len(urls) > max_urls:
    urls = urls[:max_urls]
```

This allows:
- Empty field = no limit (None)
- Numeric value = apply limit

## Edge Cases Handled

### 1. Empty Max URLs Field
- JavaScript sends `null` instead of empty string
- Backend treats `None/null` as "no limit"

### 2. Float Batch Delay
- Accepts both integers and floats
- Allows precise timing (e.g., 0.5, 1.5, 2.3 seconds)

### 3. Invalid Types
- Server validates types before processing
- Returns descriptive error messages

### 4. Boundary Values
- batch_size=1: Process one URL at a time
- batch_delay=0: No delays (maximum speed)
- max_urls=1: Test single URL only

## Files Modified

- ✅ [templates/index.html](templates/index.html) - Added 3 input fields and updated JavaScript
- ✅ [app.py](app.py) - Updated `/test` endpoint to accept and use parameters
- ✅ [test_configurable_batching.py](test_configurable_batching.py) - New test file with 6 test cases

## Future Enhancements

### Short Term
1. Show estimated processing time based on batch settings
2. Add presets: "Fast", "Normal", "Conservative"
3. Save user's preferred settings to localStorage

### Long Term
1. Dynamic batch size adjustment based on response times
2. Retry logic for failed batches
3. Progress indicator showing current batch number
4. Per-domain rate limiting configuration

## Testing

Run the configurable batching tests:
```bash
python3 -m unittest test_configurable_batching -v
```

Run all tests:
```bash
python3 -m unittest discover -v
```

## Backwards Compatibility

✅ **Fully backwards compatible**
- All new parameters are optional
- Defaults match previous hardcoded behavior
- Existing API clients continue working without changes
- UI shows sensible defaults in form fields

## Summary

The configurable batch processing feature provides users with full control over how URLs are processed during cache testing. Users can:
- Adjust batch size (1-100 URLs per batch)
- Configure delays between batches (0-10 seconds)
- Limit total URLs processed (optional max_urls)

All parameters have sensible defaults and comprehensive validation on both client and server side. The feature is fully tested with 6 unit tests and maintains backward compatibility with existing integrations.
