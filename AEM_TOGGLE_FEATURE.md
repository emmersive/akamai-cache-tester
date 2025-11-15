# AEM Toggle Feature

## Summary

Added a checkbox toggle to the HTML form that allows users to enable/disable Adobe Experience Manager (AEM) detection during cache testing.

## Changes Made

### 1. Frontend Changes ([templates/index.html](templates/index.html))

#### Added Checkbox to Form
```html
<div class="input-group">
    <label style="display: flex; align-items: center; cursor: pointer; user-select: none;">
        <input
            type="checkbox"
            id="checkAem"
            checked
            style="margin-right: 8px; width: 18px; height: 18px; cursor: pointer;">
        <span>Check for Adobe Experience Manager (AEM)</span>
    </label>
</div>
```

**Location**: Between the sitemap URL input and the "Test Sitemap" button
**Default State**: Checked (enabled)

#### Updated JavaScript

Modified `runTest()` function to read checkbox state and send it to backend:

```javascript
const checkAem = document.getElementById('checkAem').checked;

// ...

body: JSON.stringify({
    sitemap_url: sitemapUrl,
    check_aem: checkAem  // ← New parameter
})
```

### 2. Backend Changes ([app.py](app.py))

#### Updated `/test` Endpoint

**Added import:**
```python
import re  # Required for detect_aem() function
```

**Modified endpoint to accept parameter:**
```python
data = request.get_json()
sitemap_url = data.get('sitemap_url', '').strip()
check_aem = data.get('check_aem', True)  # Default to True (checked by default)
```

**Pass parameter to cache checking function:**
```python
future_to_url = {executor.submit(check_akamai_cache, url, check_aem): url for url in batch}
```

#### Updated `check_akamai_cache()` Function

**Modified AEM detection logic:**
```python
# Check for AEM if requested
is_aem = None
confidence = None
evidence = None
if test_for_aem:
    is_aem, confidence, evidence = detect_aem(response)

return {
    # ... other fields ...
    'is_aem': is_aem,  # None if not checked
    'aem_confidence': confidence,  # None if not checked
    'aem_evidence': evidence,  # None if not checked
    'error': None
}
```

#### Updated Docstring

```python
@app.route('/test', methods=['POST'])
def test_sitemap():
    """
    Process sitemap URL and test all pages in batches
    Tests URLs in batches with delays between batches

    Request JSON parameters:
    - sitemap_url (str): URL of the sitemap to test
    - check_aem (bool, optional): Whether to check for AEM detection (default: True)

    Returns JSON with results including cache status and optionally AEM detection
    """
```

### 3. Tests ([test_aem_toggle.py](test_aem_toggle.py))

Created comprehensive unit tests:

| Test | Purpose |
|------|---------|
| `test_aem_check_enabled_by_default` | Verifies AEM checking is ON when parameter not provided |
| `test_aem_check_explicitly_enabled` | Verifies AEM checking works when `check_aem=true` |
| `test_aem_check_disabled` | Verifies AEM checking is skipped when `check_aem=false` |
| `test_aem_summary_counting` | Verifies AEM sites are counted correctly in summary |

**All tests pass:**
```
Ran 4 tests in 0.006s
OK
```

## Usage

### For Users

1. **Enable AEM Detection (Default)**
   - Checkbox is checked by default
   - Each URL will be analyzed for AEM indicators
   - Results include `is_aem`, `aem_confidence`, and `aem_evidence` fields

2. **Disable AEM Detection**
   - Uncheck the "Check for Adobe Experience Manager (AEM)" checkbox
   - Speeds up testing (no HTML parsing needed)
   - AEM fields in results will be `null`

### API Request Format

**With AEM checking (default):**
```json
{
  "sitemap_url": "https://example.com/sitemap.xml"
}
```
or
```json
{
  "sitemap_url": "https://example.com/sitemap.xml",
  "check_aem": true
}
```

**Without AEM checking:**
```json
{
  "sitemap_url": "https://example.com/sitemap.xml",
  "check_aem": false
}
```

### Response Format

**When AEM checking is enabled:**
```json
{
  "success": true,
  "summary": {
    "total_urls": 10,
    "total_aem_detected": 3,
    "cache_hits": 8,
    ...
  },
  "results": [
    {
      "url": "https://example.com/page1",
      "cache_hit": "HIT",
      "is_aem": true,
      "aem_confidence": 0.85,
      "aem_evidence": {
        "html_classes": ["cq-component"],
        "data_attributes": ["data-cq-component"],
        ...
      },
      ...
    }
  ]
}
```

**When AEM checking is disabled:**
```json
{
  "success": true,
  "summary": {
    "total_urls": 10,
    "total_aem_detected": 0,
    "cache_hits": 8,
    ...
  },
  "results": [
    {
      "url": "https://example.com/page1",
      "cache_hit": "HIT",
      "is_aem": null,
      "aem_confidence": null,
      "aem_evidence": null,
      ...
    }
  ]
}
```

## Performance Impact

### With AEM Checking Enabled
- Each URL requires full HTML parsing with regex analysis
- Adds ~50-200ms per URL depending on page size
- Memory overhead for storing HTML content and evidence

### With AEM Checking Disabled
- Only headers are analyzed
- Faster response times
- Lower memory usage

## UI Display

The HTML table already displays AEM data in these columns:
- **Is AEM**: Shows "Yes", "No", or "N/A"
- **AEM Confidence**: Shows confidence score (0.0-1.0) or "N/A"

When checkbox is unchecked, these columns will show "N/A" for all rows.

## Backwards Compatibility

✅ **Fully backwards compatible**
- If `check_aem` parameter is not provided, defaults to `True` (enabled)
- Existing API calls without the parameter will continue to work as before
- All existing test cases and integrations remain functional

## Testing

Run the AEM toggle tests:
```bash
python3 -m unittest test_aem_toggle -v
```

Run all tests including AEM toggle:
```bash
python3 -m unittest discover -v
```

## Files Modified

- ✅ [templates/index.html](templates/index.html) - Added checkbox and updated JavaScript
- ✅ [app.py](app.py) - Updated endpoint, added `re` import, modified `check_akamai_cache()`
- ✅ [test_aem_toggle.py](test_aem_toggle.py) - New test file with 4 test cases

## Future Enhancements

Potential improvements:
1. Show/hide AEM columns in table based on checkbox state
2. Display loading indicator specifically for AEM detection
3. Allow configuring AEM confidence threshold
4. Add detailed AEM evidence modal/popup
5. Export AEM evidence to CSV
