"""
Test to verify AEM toggle functionality
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from app import app


class TestAemToggle(unittest.TestCase):
    """Test cases for AEM detection toggle"""

    def setUp(self):
        """Set up test client before each test"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()

    @patch('app.detect_aem')
    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_aem_check_enabled_by_default(self, mock_parse, mock_check, mock_detect):
        """Test that AEM checking is enabled by default when not specified"""
        mock_parse.return_value = ['https://example.com/page1']

        # Mock detect_aem return value
        mock_detect.return_value = (True, 0.85, {'html_classes': ['cq-component']})

        # Mock check_akamai_cache to simulate actual function behavior
        def mock_check_side_effect(url, test_for_aem=False):
            result = {
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
                'is_aem': True if test_for_aem else None,
                'aem_confidence': 0.85 if test_for_aem else None,
                'aem_evidence': {'html_classes': ['cq-component']} if test_for_aem else None,
                'error': None
            }
            return result

        mock_check.side_effect = mock_check_side_effect

        # Request without check_aem parameter (should default to True)
        response = self.client.post('/test',
                                    data=json.dumps({'sitemap_url': 'https://example.com/sitemap.xml'}),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify AEM was checked (test_for_aem should be True)
        mock_check.assert_called_once_with('https://example.com/page1', True)

        # Verify result contains AEM data
        self.assertEqual(data['results'][0]['is_aem'], True)
        self.assertEqual(data['results'][0]['aem_confidence'], 0.85)

    @patch('app.detect_aem')
    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_aem_check_explicitly_enabled(self, mock_parse, mock_check, mock_detect):
        """Test that AEM checking works when explicitly enabled"""
        mock_parse.return_value = ['https://example.com/page1']

        def mock_check_side_effect(url, test_for_aem=False):
            result = {
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
                'is_aem': False if test_for_aem else None,
                'aem_confidence': 0.15 if test_for_aem else None,
                'aem_evidence': {} if test_for_aem else None,
                'error': None
            }
            return result

        mock_check.side_effect = mock_check_side_effect

        # Request with check_aem=true
        response = self.client.post('/test',
                                    data=json.dumps({
                                        'sitemap_url': 'https://example.com/sitemap.xml',
                                        'check_aem': True
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify AEM was checked
        mock_check.assert_called_once_with('https://example.com/page1', True)
        self.assertEqual(data['results'][0]['is_aem'], False)

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_aem_check_disabled(self, mock_parse, mock_check):
        """Test that AEM checking is skipped when disabled"""
        mock_parse.return_value = ['https://example.com/page1']

        def mock_check_side_effect(url, test_for_aem=False):
            result = {
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
            return result

        mock_check.side_effect = mock_check_side_effect

        # Request with check_aem=false
        response = self.client.post('/test',
                                    data=json.dumps({
                                        'sitemap_url': 'https://example.com/sitemap.xml',
                                        'check_aem': False
                                    }),
                                    content_type='application/json')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)

        # Verify AEM was NOT checked (test_for_aem should be False)
        mock_check.assert_called_once_with('https://example.com/page1', False)

        # Verify result does NOT contain AEM data
        self.assertIsNone(data['results'][0]['is_aem'])
        self.assertIsNone(data['results'][0]['aem_confidence'])

    @patch('app.check_akamai_cache')
    @patch('app.parse_sitemap')
    def test_aem_summary_counting(self, mock_parse, mock_check):
        """Test that AEM detection is counted correctly in summary"""
        mock_parse.return_value = [
            'https://example.com/page1',
            'https://example.com/page2',
            'https://example.com/page3'
        ]

        # Mock results: 2 AEM sites, 1 non-AEM
        results = [
            {'is_aem': True, 'cache_hit': 'HIT', 'url': 'https://example.com/page1', 'status_code': 200,
             'x_cache': 'TCP_HIT', 'x_cache_remote': 'NOT_FOUND', 'x_check_cacheable': 'YES',
             'x_cache_key': 'key1', 'x_true_cache_key': 'true_key1', 'x_served_by': 'cache-mel11250-MEL',
             'x_timer': 'S1763167085.909978,VS0,VS0,VE1', 'age': '100', 'cache_control': 'max-age=300',
             'response_time_ms': 1, 'aem_confidence': 0.85, 'aem_evidence': {}, 'error': None},
            {'is_aem': True, 'cache_hit': 'HIT', 'url': 'https://example.com/page2', 'status_code': 200,
             'x_cache': 'TCP_HIT', 'x_cache_remote': 'NOT_FOUND', 'x_check_cacheable': 'YES',
             'x_cache_key': 'key2', 'x_true_cache_key': 'true_key2', 'x_served_by': 'cache-mel11250-MEL',
             'x_timer': 'S1763167085.909978,VS0,VS0,VE1', 'age': '100', 'cache_control': 'max-age=300',
             'response_time_ms': 1, 'aem_confidence': 0.75, 'aem_evidence': {}, 'error': None},
            {'is_aem': False, 'cache_hit': 'MISS', 'url': 'https://example.com/page3', 'status_code': 200,
             'x_cache': 'TCP_MISS', 'x_cache_remote': 'NOT_FOUND', 'x_check_cacheable': 'YES',
             'x_cache_key': 'key3', 'x_true_cache_key': 'true_key3', 'x_served_by': 'cache-mel11250-MEL',
             'x_timer': 'S1763167085.909978,VS0,VS0,VE1000', 'age': '0', 'cache_control': 'max-age=300',
             'response_time_ms': 1000, 'aem_confidence': 0.1, 'aem_evidence': {}, 'error': None}
        ]

        mock_check.side_effect = results

        response = self.client.post('/test',
                                    data=json.dumps({
                                        'sitemap_url': 'https://example.com/sitemap.xml',
                                        'check_aem': True
                                    }),
                                    content_type='application/json')

        data = json.loads(response.data)

        # Verify summary counts AEM sites correctly
        self.assertEqual(data['summary']['total_aem_detected'], 2)
        self.assertEqual(data['summary']['total_urls'], 3)


if __name__ == '__main__':
    unittest.main()
