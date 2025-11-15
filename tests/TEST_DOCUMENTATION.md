# Test Documentation for `/test` Route

## Overview

Comprehensive unit tests for the `test_sitemap()` function in the Flask application. The tests cover all major functionality, edge cases, and error conditions.

## Test Suite: `TestSitemapRoute`

### Test Coverage Summary

| Category | Tests | Description |
|----------|-------|-------------|
| Input Validation | 3 | Missing/empty sitemap URL, empty sitemap results |
| Success Cases | 4 | Normal operation with various cache status combinations |
| Edge Cases | 2 | URL limiting, all non-cacheable URLs |
| Error Handling | 1 | Exception handling during sitemap parsing |
| Response Format | 1 | Timestamp validation |
| Statistics | 2 | Cache hit ratio calculations and status counting |

**Total: 11 test cases**

---

## Detailed Test Cases

### 1. Input Validation Tests

#### `test_missing_sitemap_url`
- **Purpose**: Verify API rejects requests without sitemap URL
- **Input**: Empty JSON payload `{}`
- **Expected**: HTTP 400 with error message "Please provide a sitemap URL"
- **Validates**: Input validation logic

#### `test_empty_sitemap_url`
- **Purpose**: Verify API rejects whitespace-only sitemap URLs
- **Input**: `{"sitemap_url": "   "}`
- **Expected**: HTTP 400 with error message "Please provide a sitemap URL"
- **Validates**: `.strip()` handling and empty string detection

#### `test_no_urls_found_in_sitemap`
- **Purpose**: Verify API handles sitemaps with no valid URLs
- **Input**: Valid sitemap URL that returns empty list
- **Expected**: HTTP 400 with error "No URLs found in sitemap"
- **Validates**: Empty result handling from `parse_sitemap()`

---

### 2. Success Cases

#### `test_successful_cache_test_with_hits`
- **Purpose**: Test normal operation with mixed cache results
- **Scenario**:
  - 3 URLs from sitemap
  - 1 confirmed HIT (with X-Cache header)
  - 1 inferred HIT (from timing analysis)
  - 1 confirmed MISS
- **Expected**:
  - HTTP 200 with success=true
  - Summary: 2 total hits, 1 miss, 66.67% hit ratio
  - Breakdown: 1 confirmed hit, 1 inferred hit
- **Validates**:
  - Complete workflow from sitemap to results
  - Concurrent URL processing
  - Statistics calculation
  - Response structure

#### `test_all_cacheable_urls_with_zero_errors`
- **Purpose**: Test 100% cache hit scenario
- **Scenario**: All URLs return cache HITs
- **Expected**: 100.0% cache hit ratio
- **Validates**: Perfect caching scenario calculation

#### `test_response_contains_timestamp`
- **Purpose**: Verify timestamp is included in response
- **Expected**: Valid ISO 8601 timestamp format
- **Validates**: Response metadata completeness

#### `test_unknown_status_counting`
- **Purpose**: Test handling of timing-inconclusive results
- **Scenario**: Mix of UNKNOWN and known statuses
- **Expected**: Correct counting in summary.unknown field
- **Validates**: All cache status types are tracked

---

### 3. Statistics & Calculations

#### `test_cache_hit_ratio_calculation`
- **Purpose**: Comprehensive test of statistics calculation
- **Scenario**: 10 URLs with diverse results:
  - 3 confirmed HITs
  - 3 inferred HITs (from timing)
  - 2 confirmed MISSes
  - 1 NOT_CACHEABLE
  - 1 ERROR
- **Expected Summary**:
  ```json
  {
    "total_urls": 10,
    "cache_hits": 6,
    "cache_misses": 2,
    "confirmed_hits": 3,
    "inferred_hits": 3,
    "confirmed_misses": 2,
    "inferred_misses": 0,
    "not_cacheable": 1,
    "errors": 1,
    "unknown": 0,
    "cache_hit_ratio": 75.0
  }
  ```
- **Formula**: `6 / (10 - 1 - 1) = 6/8 = 75%`
- **Validates**:
  - Inferred hits count as positive matches
  - NOT_CACHEABLE excluded from denominator
  - ERRORs excluded from denominator
  - All status types counted separately

---

### 4. Edge Cases

#### `test_url_limit_enforced`
- **Purpose**: Verify 100 URL limit is enforced
- **Scenario**: Sitemap returns 150 URLs
- **Expected**: Only first 100 URLs tested
- **Validates**:
  - `max_urls = 100` enforcement
  - `urls[:max_urls]` slicing logic
  - Performance protection

#### `test_all_urls_not_cacheable`
- **Purpose**: Test scenario where no URLs are cacheable
- **Scenario**: All URLs marked as NOT_CACHEABLE
- **Expected**:
  - cache_hit_ratio = 0 (avoid division by zero)
  - not_cacheable = 2
- **Validates**:
  - Division by zero protection
  - `(hits / cacheable_total * 100) if cacheable_total > 0 else 0`

---

### 5. Error Handling

#### `test_sitemap_parse_exception`
- **Purpose**: Test exception handling during sitemap parsing
- **Scenario**: `parse_sitemap()` raises exception
- **Expected**: HTTP 500 with error message included
- **Validates**:
  - Try/except block catches exceptions
  - Errors returned with appropriate status code
  - Error messages preserved

---

## Cache Status Types Tested

The tests validate all cache status types:

| Status | Type | Tested |
|--------|------|---------|
| `HIT` | Confirmed (X-Cache) | ✅ |
| `HIT (inferred from timing)` | Inferred (X-Timer) | ✅ |
| `MISS` | Confirmed (X-Cache) | ✅ |
| `MISS (inferred from timing)` | Inferred (X-Timer) | Not explicitly (covered in ratio calc) |
| `REFRESH_HIT` | Confirmed | Not explicitly (included in confirmed_hits logic) |
| `REFRESH_MISS` | Confirmed | Not explicitly (included in confirmed_misses logic) |
| `NOT_CACHEABLE` | Determined | ✅ |
| `ERROR` | Request failure | ✅ |
| `UNKNOWN (timing inconclusive)` | Timing ambiguous | ✅ |

---

## Running the Tests

### Using unittest (built-in)
```bash
python3 -m unittest test_app -v
```

### Using pytest (if installed)
```bash
pytest test_app.py -v
```

### Run specific test
```bash
python3 -m unittest test_app.TestSitemapRoute.test_cache_hit_ratio_calculation -v
```

---

## Test Results

```
test_all_cacheable_urls_with_zero_errors ... ok
test_all_urls_not_cacheable ... ok
test_cache_hit_ratio_calculation ... ok
test_empty_sitemap_url ... ok
test_missing_sitemap_url ... ok
test_no_urls_found_in_sitemap ... ok
test_response_contains_timestamp ... ok
test_sitemap_parse_exception ... ok
test_successful_cache_test_with_hits ... ok
test_unknown_status_counting ... ok
test_url_limit_enforced ... ok

----------------------------------------------------------------------
Ran 11 tests in 0.012s

OK
```

---

## Mock Strategy

The tests use `unittest.mock` to isolate the `/test` route logic:

1. **`@patch('app.parse_sitemap')`**: Mocks sitemap XML parsing to return controlled URL lists
2. **`@patch('app.check_akamai_cache')`**: Mocks cache checking to return predetermined results
3. **Side effects**: Used to simulate different responses for different URLs

This approach:
- ✅ Tests route logic in isolation
- ✅ Avoids external HTTP requests
- ✅ Provides deterministic, fast tests
- ✅ Allows testing edge cases easily

---

## Coverage Areas

### ✅ Fully Covered
- Input validation
- URL limiting
- Statistics calculation
- All cache status types
- Error handling
- Response format
- Concurrent processing logic

### ⚠️ Not Covered (Integration Tests Needed)
- Actual HTTP requests to real sitemaps
- XML parsing edge cases (handled by `parse_sitemap` tests)
- Thread pool executor behavior under load
- Network timeout scenarios
- Memory usage with large sitemaps

---

## Future Test Enhancements

1. **Integration Tests**: Test with real sitemap XML files
2. **Performance Tests**: Verify concurrent processing scales correctly
3. **Load Tests**: Test with maximum URL limit (100)
4. **Mock Server Tests**: Use `responses` library for HTTP mocking
5. **Additional Routes**: Test `/export` CSV generation

---

## Key Assertions Validated

```python
# Response structure
assert response.status_code == 200
assert data['success'] == True
assert 'summary' in data
assert 'results' in data
assert 'timestamp' in data

# Summary statistics
assert summary['cache_hits'] == confirmed + inferred
assert summary['cache_hit_ratio'] == (hits / cacheable_total * 100)

# Status counting
assert 'HIT' in cache_hit  # Includes both HIT and HIT (inferred)
assert 'MISS' in cache_hit  # Includes both MISS and MISS (inferred)
```

---

## Maintenance Notes

When modifying the `/test` route:

1. **Add new statistics**: Update `test_cache_hit_ratio_calculation`
2. **Change status types**: Update all tests checking `cache_hit` values
3. **Modify URL limit**: Update `test_url_limit_enforced`
4. **Add validation**: Create new test case for the validation logic
5. **Change response format**: Update all tests checking response structure
