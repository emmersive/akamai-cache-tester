"""
Test different header combinations to find cache status indicators
"""
import requests
import json

TEST_URL = "https://www.optus.com.au/sitemap.xml"

# Base headers
BASE_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8,en-AU;q=0.7',
    'cache-control': 'no-cache',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36'
}

# Different Pragma variations to test
PRAGMA_TESTS = [
    ("Standard Pragma (multi)", {
        'pragma': 'akamai-x-cache-on, akamai-x-cache-remote-on, akamai-x-check-cacheable, akamai-x-get-cache-key, akamai-x-get-true-cache-key'
    }),
    ("Single Pragma", {
        'pragma': 'akamai-x-cache-on'
    }),
    ("Separate Akamai Headers", {
        'Akamai-X-Cache-On': '1',
        'Akamai-X-Cache-Remote-On': '1',
        'Akamai-X-Check-Cacheable': '1'
    }),
    ("X-Akamai-Session-Info", {
        'X-Akamai-Session-Info': 'name=AKA_PM_CACHEABLE_OBJECT;value=true'
    }),
    ("No special headers", {})
]

# Cache-related headers to look for in response
CACHE_HEADERS = [
    'X-Cache', 'X-Cache-Remote', 'X-Check-Cacheable', 'X-Cache-Key', 'X-True-Cache-Key',
    'Age', 'X-Served-By', 'Via', 'X-Timer', 'CF-Cache-Status', 'X-Cache-Status',
    'X-Akamai-Transformed', 'Akamai-GRN', 'X-Akamai-Request-ID', 'X-Akamai-Session-Info',
    'Cache-Control', 'ETag', 'Last-Modified', 'Vary'
]

def test_headers():
    print(f"Testing URL: {TEST_URL}\n")
    print("=" * 80)

    for test_name, extra_headers in PRAGMA_TESTS:
        print(f"\n### Test: {test_name}")
        print(f"Extra headers: {extra_headers}")
        print("-" * 80)

        headers = {**BASE_HEADERS, **extra_headers}

        try:
            response = requests.get(TEST_URL, headers=headers, timeout=30)
            print(f"Status Code: {response.status_code}")

            # Check for cache-related headers
            found_headers = {}
            for header in CACHE_HEADERS:
                value = response.headers.get(header)
                if value:
                    found_headers[header] = value

            if found_headers:
                print("\nCache-related headers found:")
                for key, value in found_headers.items():
                    print(f"  {key}: {value}")
            else:
                print("\nNo cache-related headers found")

        except requests.exceptions.Timeout:
            print("❌ Request timed out")
        except Exception as e:
            print(f"❌ Error: {str(e)}")

        print("=" * 80)

if __name__ == "__main__":
    test_headers()
