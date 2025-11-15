"""
Test to verify configurable batch processing parameters
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from app import app


class TestConfigurableBatching(unittest.TestCase):
    """Test cases for configurable batch processing"""

    def setUp(self):
        """Set up test client before each test"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_default_batch_parameters(self, mock_parse, mock_check):
        """Test that default batch parameters are used when not specified"""
        mock_parse.return_value = ['https://example.com/page1']

        def mock_check_side_effect(url, test_for_aem=False):
            return {
                'url': url,
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
                'is_aem': None,
                'aem_confidence': None,
                'aem_evidence': None,
                'error': None
            }

        mock_check.side_effect = mock_check_side_effect

        # Request without batch parameters (should use defaults)
        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data['success'])

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_custom_batch_size(self, mock_parse, mock_check):
        """Test that custom batch size is used"""
        mock_parse.return_value = [
            'https://example.com/page1',
            'https://example.com/page2',
            'https://example.com/page3',
            'https://example.com/page4',
            'https://example.com/page5'
        ]

        def mock_check_side_effect(url, test_for_aem=False):
            return {
                'url': url,
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
                'is_aem': None,
                'aem_confidence': None,
                'aem_evidence': None,
                'error': None
            }

        mock_check.side_effect = mock_check_side_effect

        # Request with custom batch_size=2
        response = self.client.post('/test',
                                    data=json.dumps({
                                        'sitemap_url': 'https://example.com/sitemap.xml',
                                        'batch_size': 2
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['summary']['total_urls'], 5)

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_max_urls_limit(self, mock_parse, mock_check):
        """Test that max_urls limit is applied"""
        mock_parse.return_value = [f'https://example.com/page{i}' for i in range(1, 11)]

        def mock_check_side_effect(url, test_for_aem=False):
            return {
                'url': url,
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
                'is_aem': None,
                'aem_confidence': None,
                'aem_evidence': None,
                'error': None
            }

        mock_check.side_effect = mock_check_side_effect

        # Request with max_urls=5 (should only process 5 URLs)
        response = self.client.post('/test',
                                    data=json.dumps({
                                        'sitemap_url': 'https://example.com/sitemap.xml',
                                        'max_urls': 5
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['summary']['total_urls'], 5)

    def test_invalid_batch_size(self):
        """Test that invalid batch size returns error"""
        response = self.client.post('/test',
                                    data=json.dumps({
                                        'sitemap_url': 'https://example.com/sitemap.xml',
                                        'batch_size': 0
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Batch size', data['error'])

    def test_invalid_batch_delay(self):
        """Test that invalid batch delay returns error"""
        response = self.client.post('/test',
                                    data=json.dumps({
                                        'sitemap_url': 'https://example.com/sitemap.xml',
                                        'batch_delay': -1
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Batch delay', data['error'])

    def test_invalid_max_urls(self):
        """Test that invalid max_urls returns error"""
        response = self.client.post('/test',
                                    data=json.dumps({
                                        'sitemap_url': 'https://example.com/sitemap.xml',
                                        'max_urls': 0
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('Max URLs', data['error'])


if __name__ == '__main__':
    unittest.main()
