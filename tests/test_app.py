"""
Unit tests for the Akamai Cache Tester Flask application
Tests the /test route and related functions
"""

import unittest
from unittest.mock import patch, MagicMock, Mock
import json
from datetime import datetime
from app import app, check_akamai_cache, parse_sitemap


class TestSitemapRoute(unittest.TestCase):
    """Test cases for the /test route"""

    def setUp(self):
        """Set up test client before each test"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    def test_missing_sitemap_url(self):
        """Test that missing sitemap URL returns 400 error"""
        response = self.client.post('/test',
                                    data=json.dumps({}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Please provide a sitemap URL')

    def test_empty_sitemap_url(self):
        """Test that empty sitemap URL returns 400 error"""
        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': '   '}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Please provide a sitemap URL')

    @patch('app.parse_sitemap')
    def test_no_urls_found_in_sitemap(self, mock_parse):
        """Test that sitemap with no URLs returns 400 error"""
        mock_parse.return_value = []

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No URLs found in sitemap')

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_successful_cache_test_with_hits(self, mock_parse, mock_check):
        """Test successful cache testing with cache hits"""
        # Mock sitemap parsing
        mock_parse.return_value = [
            'https://example.com/page1',
            'https://example.com/page2',
            'https://example.com/page3'
        ]

        # Mock cache checking with different results
        mock_check.side_effect = [
            {
                'url': 'https://example.com/page1',
                'status_code': 200,
                'cache_hit': 'HIT',
                'x_cache': 'TCP_HIT',
                'x_cache_remote': 'TCP_HIT',
                'x_check_cacheable': 'YES',
                'x_cache_key': 'key1',
                'x_true_cache_key': 'true_key1',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE1',
                'age': '100',
                'cache_control': 'max-age=300',
                'response_time_ms': 1,
                'error': None
            },
            {
                'url': 'https://example.com/page2',
                'status_code': 200,
                'cache_hit': 'HIT (inferred from timing)',
                'x_cache': 'NOT_FOUND',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'UNKNOWN',
                'x_cache_key': 'NOT_FOUND',
                'x_true_cache_key': 'NOT_FOUND',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE50',
                'age': '0',
                'cache_control': 'max-age=300',
                'response_time_ms': 50,
                'error': None
            },
            {
                'url': 'https://example.com/page3',
                'status_code': 200,
                'cache_hit': 'MISS',
                'x_cache': 'TCP_MISS',
                'x_cache_remote': 'TCP_MISS',
                'x_check_cacheable': 'YES',
                'x_cache_key': 'key3',
                'x_true_cache_key': 'true_key3',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE1000',
                'age': '0',
                'cache_control': 'max-age=300',
                'response_time_ms': 1000,
                'error': None
            }
        ]

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify response structure
        self.assertTrue(data['success'])
        self.assertIn('summary', data)
        self.assertIn('results', data)
        self.assertIn('timestamp', data)

        # Verify summary statistics
        summary = data['summary']
        self.assertEqual(summary['total_urls'], 3)
        self.assertEqual(summary['cache_hits'], 2)  # 1 confirmed + 1 inferred
        self.assertEqual(summary['cache_misses'], 1)
        self.assertEqual(summary['confirmed_hits'], 1)
        self.assertEqual(summary['inferred_hits'], 1)
        self.assertEqual(summary['confirmed_misses'], 1)
        self.assertEqual(summary['not_cacheable'], 0)
        self.assertEqual(summary['errors'], 0)
        self.assertEqual(summary['cache_hit_ratio'], 66.67)  # 2/3 * 100

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_cache_hit_ratio_calculation(self, mock_parse, mock_check):
        """Test that cache hit ratio is calculated correctly"""
        mock_parse.return_value = [f'https://example.com/page{i}' for i in range(10)]

        # Create mixed results: 6 hits, 2 misses, 1 not_cacheable, 1 error
        results = []
        for i in range(6):
            results.append({
                'url': f'https://example.com/page{i}',
                'cache_hit': 'HIT' if i < 3 else 'HIT (inferred from timing)',
                'status_code': 200,
                'x_cache': 'TCP_HIT' if i < 3 else 'NOT_FOUND',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'YES',
                'x_cache_key': f'key{i}',
                'x_true_cache_key': f'true_key{i}',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE1',
                'age': '100' if i < 3 else '0',
                'cache_control': 'max-age=300',
                'response_time_ms': 1,
                'error': None
            })

        for i in range(6, 8):
            results.append({
                'url': f'https://example.com/page{i}',
                'cache_hit': 'MISS',
                'status_code': 200,
                'x_cache': 'TCP_MISS',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'YES',
                'x_cache_key': f'key{i}',
                'x_true_cache_key': f'true_key{i}',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE1000',
                'age': '0',
                'cache_control': 'max-age=300',
                'response_time_ms': 1000,
                'error': None
            })

        results.append({
            'url': 'https://example.com/page8',
            'cache_hit': 'NOT_CACHEABLE',
            'status_code': 200,
            'x_cache': 'NOT_FOUND',
            'x_cache_remote': 'NOT_FOUND',
            'x_check_cacheable': 'NO',
            'x_cache_key': 'NOT_FOUND',
            'x_true_cache_key': 'NOT_FOUND',
            'x_served_by': 'cache-mel11250-MEL',
            'x_timer': 'NOT_FOUND',
            'age': '0',
            'cache_control': 'no-cache',
            'response_time_ms': None,
            'error': None
        })

        results.append({
            'url': 'https://example.com/page9',
            'cache_hit': 'ERROR',
            'status_code': 'ERROR',
            'x_cache': 'ERROR',
            'x_cache_remote': 'ERROR',
            'x_check_cacheable': 'ERROR',
            'x_cache_key': 'ERROR',
            'x_true_cache_key': 'ERROR',
            'x_served_by': 'ERROR',
            'x_timer': 'ERROR',
            'age': 'ERROR',
            'cache_control': 'ERROR',
            'response_time_ms': None,
            'error': 'Connection timeout'
        })

        mock_check.side_effect = results

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        data = json.loads(response.data)
        summary = data['summary']

        # Verify counts
        self.assertEqual(summary['total_urls'], 10)
        self.assertEqual(summary['cache_hits'], 6)
        self.assertEqual(summary['cache_misses'], 2)
        self.assertEqual(summary['confirmed_hits'], 3)
        self.assertEqual(summary['inferred_hits'], 3)
        self.assertEqual(summary['not_cacheable'], 1)
        self.assertEqual(summary['errors'], 1)

        # Cache hit ratio = 6 / (10 - 1 not_cacheable - 1 error) = 6/8 = 75%
        self.assertEqual(summary['cache_hit_ratio'], 75.0)

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_url_limit_enforced(self, mock_parse, mock_check):
        """Test that URLs are limited to max_urls (100)"""
        # Return 150 URLs
        urls = [f'https://example.com/page{i}' for i in range(150)]
        mock_parse.return_value = urls

        # Mock should only be called 100 times
        mock_check.return_value = {
            'url': 'https://example.com/page1',
            'cache_hit': 'HIT',
            'status_code': 200,
            'x_cache': 'TCP_HIT',
            'x_cache_remote': 'NOT_FOUND',
            'x_check_cacheable': 'YES',
            'x_cache_key': 'key',
            'x_true_cache_key': 'true_key',
            'x_served_by': 'cache-mel11250-MEL',
            'x_timer': 'S1763167085.909978,VS0,VS0,VE1',
            'age': '100',
            'cache_control': 'max-age=300',
            'response_time_ms': 1,
            'error': None
        }

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        data = json.loads(response.data)

        # Verify only 100 URLs were tested
        self.assertEqual(data['summary']['total_urls'], 100)
        self.assertEqual(mock_check.call_count, 100)

    @patch('app.parse_sitemap')
    def test_sitemap_parse_exception(self, mock_parse):
        """Test that sitemap parsing exceptions are handled"""
        mock_parse.side_effect = Exception('Failed to parse sitemap XML')

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
        self.assertIn('Failed to parse sitemap XML', data['error'])

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_all_cacheable_urls_with_zero_errors(self, mock_parse, mock_check):
        """Test cache hit ratio when all URLs are cacheable"""
        mock_parse.return_value = ['https://example.com/page1', 'https://example.com/page2']

        mock_check.side_effect = [
            {
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
            },
            {
                'url': 'https://example.com/page2',
                'cache_hit': 'HIT',
                'status_code': 200,
                'x_cache': 'TCP_HIT',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'YES',
                'x_cache_key': 'key2',
                'x_true_cache_key': 'true_key2',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE1',
                'age': '100',
                'cache_control': 'max-age=300',
                'response_time_ms': 1,
                'error': None
            }
        ]

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        data = json.loads(response.data)
        summary = data['summary']

        # 100% cache hit ratio
        self.assertEqual(summary['cache_hit_ratio'], 100.0)

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_all_urls_not_cacheable(self, mock_parse, mock_check):
        """Test cache hit ratio when all URLs are not cacheable (should be 0)"""
        mock_parse.return_value = ['https://example.com/page1', 'https://example.com/page2']

        mock_check.side_effect = [
            {
                'url': 'https://example.com/page1',
                'cache_hit': 'NOT_CACHEABLE',
                'status_code': 200,
                'x_cache': 'NOT_FOUND',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'NO',
                'x_cache_key': 'NOT_FOUND',
                'x_true_cache_key': 'NOT_FOUND',
                'x_served_by': 'NOT_FOUND',
                'x_timer': 'NOT_FOUND',
                'age': '0',
                'cache_control': 'no-cache',
                'response_time_ms': None,
                'error': None
            },
            {
                'url': 'https://example.com/page2',
                'cache_hit': 'NOT_CACHEABLE',
                'status_code': 200,
                'x_cache': 'NOT_FOUND',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'NO',
                'x_cache_key': 'NOT_FOUND',
                'x_true_cache_key': 'NOT_FOUND',
                'x_served_by': 'NOT_FOUND',
                'x_timer': 'NOT_FOUND',
                'age': '0',
                'cache_control': 'no-cache',
                'response_time_ms': None,
                'error': None
            }
        ]

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        data = json.loads(response.data)
        summary = data['summary']

        # Cache hit ratio should be 0 when cacheable_total is 0
        self.assertEqual(summary['cache_hit_ratio'], 0)
        self.assertEqual(summary['not_cacheable'], 2)

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_response_contains_timestamp(self, mock_parse, mock_check):
        """Test that response includes ISO format timestamp"""
        mock_parse.return_value = ['https://example.com/page1']
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

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        data = json.loads(response.data)

        # Verify timestamp is present and valid ISO format
        self.assertIn('timestamp', data)
        # Should be parseable as ISO format
        datetime.fromisoformat(data['timestamp'])

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_unknown_status_counting(self, mock_parse, mock_check):
        """Test that UNKNOWN statuses are counted correctly"""
        mock_parse.return_value = ['https://example.com/page1', 'https://example.com/page2']

        mock_check.side_effect = [
            {
                'url': 'https://example.com/page1',
                'cache_hit': 'UNKNOWN (timing inconclusive)',
                'status_code': 200,
                'x_cache': 'NOT_FOUND',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'UNKNOWN',
                'x_cache_key': 'NOT_FOUND',
                'x_true_cache_key': 'NOT_FOUND',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE250',
                'age': '0',
                'cache_control': 'max-age=300',
                'response_time_ms': 250,
                'error': None
            },
            {
                'url': 'https://example.com/page2',
                'cache_hit': 'HIT',
                'status_code': 200,
                'x_cache': 'TCP_HIT',
                'x_cache_remote': 'NOT_FOUND',
                'x_check_cacheable': 'YES',
                'x_cache_key': 'key2',
                'x_true_cache_key': 'true_key2',
                'x_served_by': 'cache-mel11250-MEL',
                'x_timer': 'S1763167085.909978,VS0,VS0,VE1',
                'age': '100',
                'cache_control': 'max-age=300',
                'response_time_ms': 1,
                'error': None
            }
        ]

        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        data = json.loads(response.data)
        summary = data['summary']

        self.assertEqual(summary['unknown'], 1)
        self.assertEqual(summary['cache_hits'], 1)


if __name__ == '__main__':
    unittest.main()
