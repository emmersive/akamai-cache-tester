"""
Test to verify batch processing with delays
"""
import time
from unittest.mock import patch, MagicMock
import json
from app import app


def test_batch_processing_with_delay():
    """Test that URLs are processed in batches with 1-second delays"""

    # Set up test client
    test_app = app
    test_app.config['TESTING'] = True
    client = test_app.test_client()

    # Create 25 test URLs (should result in 3 batches: 10, 10, 5)
    test_urls = [f'https://example.com/page{i}' for i in range(25)]

    # Mock parse_sitemap to return our test URLs
    with patch('app.parse_sitemap') as mock_parse:
        mock_parse.return_value = test_urls

        # Mock check_akamai_cache to return quickly
        with patch('app.check_akamai_cache') as mock_check:
            mock_check.return_value = {
                'url': 'https://example.com/page1',
                'cache_hit': 'HIT',
                'status_code': 200,
                'x_cache': 'TCP_HIT',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'YES',
                'x_cache_key': 'key1',
                'x_true_cache_key': 'true_key1',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE1',
                'age': '100',
                'cache_control': 'max-age=300',
                'response_time_ms': 1,
                'error': None
            }

            # Time the request
            start_time = time.time()

            response = client.post('/test',
                                  data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                  content_type='application/json')

            end_time = time.time()
            elapsed_time = end_time - start_time

            # Verify response
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] == True
            assert data['summary']['total_urls'] == 25

            # Verify batching occurred
            # With 25 URLs in batches of 10, we should have:
            # - Batch 1: URLs 0-9 (10 URLs)
            # - Wait 1 second
            # - Batch 2: URLs 10-19 (10 URLs)
            # - Wait 1 second
            # - Batch 3: URLs 20-24 (5 URLs, no wait after)
            # Total delay should be ~2 seconds (2 waits between 3 batches)

            print(f"\nBatch Processing Test Results:")
            print(f"URLs processed: {data['summary']['total_urls']}")
            print(f"Total time: {elapsed_time:.2f} seconds")
            print(f"Expected minimum time: ~2 seconds (2 delays between 3 batches)")

            # Assert that we had at least 2 seconds of delays
            # (allowing some overhead for processing)
            assert elapsed_time >= 2.0, f"Expected at least 2s delay, got {elapsed_time:.2f}s"
            assert elapsed_time < 5.0, f"Expected less than 5s total, got {elapsed_time:.2f}s (too slow)"

            print(f"✅ Batch processing working correctly!")
            print(f"✅ Delays between batches confirmed")


if __name__ == '__main__':
    test_batch_processing_with_delay()
    print("\n✅ All batch processing tests passed!")
