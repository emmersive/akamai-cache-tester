"""
Unit tests for batch processing with delays
Compatible with VS Code test discovery
"""
import unittest
import time
from unittest.mock import patch
import json
from app import app, URL_BATCH_SIZE, BATCH_DELAY


class TestBatchProcessing(unittest.TestCase):
    """Test cases for batch processing functionality"""

    def setUp(self):
        """Set up test client before each test"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_batch_processing_with_delay(self):
        """Test that URLs are processed in batches with delays between batches"""

        # Create 25 test URLs
        # With URL_BATCH_SIZE=3, this should create: 3+3+3+3+3+3+3+3+1 = 9 batches
        # Which means 8 delays between batches
        test_urls = [f'https://example.com/page{i}' for i in range(25)]

        with patch('app.parse_sitemap') as mock_parse:
            mock_parse.return_value = test_urls

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

                response = self.client.post('/test',
                                          data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                          content_type='application/json')

                end_time = time.time()
                elapsed_time = end_time - start_time

                # Verify response
                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertTrue(data['success'])
                self.assertEqual(data['summary']['total_urls'], 25)

                # Calculate expected batches and delays
                num_batches = (len(test_urls) + URL_BATCH_SIZE - 1) // URL_BATCH_SIZE
                num_delays = num_batches - 1
                expected_min_delay = num_delays * BATCH_DELAY

                # Verify batching occurred with proper delays
                self.assertGreaterEqual(elapsed_time, expected_min_delay,
                                      f"Expected at least {expected_min_delay}s delay, got {elapsed_time:.2f}s")
                self.assertLess(elapsed_time, expected_min_delay + 5.0,
                               f"Expected less than {expected_min_delay + 5}s total, got {elapsed_time:.2f}s")

    def test_batch_size_configuration(self):
        """Test that batch size is properly configured"""
        self.assertIsInstance(URL_BATCH_SIZE, int)
        self.assertGreater(URL_BATCH_SIZE, 0)
        self.assertIsInstance(BATCH_DELAY, (int, float))
        self.assertGreaterEqual(BATCH_DELAY, 0)

    def test_single_batch_no_delay(self):
        """Test that single batch (URLs <= batch_size) has no delay"""

        # Create URLs equal to batch size (should be 1 batch, no delay)
        test_urls = [f'https://example.com/page{i}' for i in range(URL_BATCH_SIZE)]

        with patch('app.parse_sitemap') as mock_parse:
            mock_parse.return_value = test_urls

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

                start_time = time.time()

                response = self.client.post('/test',
                                          data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                          content_type='application/json')

                end_time = time.time()
                elapsed_time = end_time - start_time

                # Should complete quickly with no batch delay
                self.assertEqual(response.status_code, 200)
                self.assertLess(elapsed_time, 2.0,
                              f"Single batch should complete quickly, took {elapsed_time:.2f}s")

    def test_exact_multiple_batches(self):
        """Test URLs that are exact multiple of batch size"""

        # Create URLs that are exactly 3x batch size
        num_urls = URL_BATCH_SIZE * 3
        test_urls = [f'https://example.com/page{i}' for i in range(num_urls)]

        with patch('app.parse_sitemap') as mock_parse:
            mock_parse.return_value = test_urls

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

                start_time = time.time()

                response = self.client.post('/test',
                                          data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                          content_type='application/json')

                end_time = time.time()
                elapsed_time = end_time - start_time

                # 3 batches = 2 delays
                expected_delays = 2
                expected_min_time = expected_delays * BATCH_DELAY

                self.assertEqual(response.status_code, 200)
                data = json.loads(response.data)
                self.assertEqual(data['summary']['total_urls'], num_urls)
                self.assertGreaterEqual(elapsed_time, expected_min_time)


if __name__ == '__main__':
    unittest.main()
