"""
Akamai Cache Testing Web Application
Fetches URLs from a sitemap.xml and tests Akamai cache status
"""

from flask import Flask, render_template, request, jsonify, send_file
import requests
from lxml import etree
import csv
import io
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from typing import Dict, Tuple
import re

app = Flask(__name__)

# Chrome user agent string
REQUEST_HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-encoding': 'gzip, deflate, br, zstd',
    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8,en-AU;q=0.7',
    'cache-control': 'no-cache',
    'priority': 'u=0, i',
    'sec-ch-ua': '"Chromium";v="142", "Microsoft Edge";v="142", "Not_A Brand";v="99"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0',
    'pragma': 'akamai-x-cache-on, akamai-x-cache-remote-on, akamai-x-check-cacheable, akamai-x-get-cache-key, akamai-x-get-true-cache-key'
}

# Akamai Pragma headers for debugging
AKAMAI_PRAGMA_HEADERS = 'akamai-x-cache-on, akamai-x-cache-remote-on, akamai-x-check-cacheable, akamai-x-get-cache-key, akamai-x-get-true-cache-key'

# Test URLs in batches to avoid overwhelming the server
URL_BATCH_SIZE = 3  # Process 10 URLs at a time
BATCH_DELAY = 1.0  # Wait 1 second between batches

def parse_sitemap(sitemap_url):
    """
    Parse sitemap.xml and extract all URLs
    Handles both regular sitemaps and sitemap indexes
    """
    try:


        response = requests.get(sitemap_url, headers=REQUEST_HEADERS, timeout=240)
        response.raise_for_status()
        
        root = etree.fromstring(response.content)
        
        # Define namespaces
        namespaces = {
            'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'
        }
        
        urls = []
        
        # Check if this is a sitemap index
        sitemap_elements = root.xpath('.//sm:sitemap/sm:loc', namespaces=namespaces)
        if sitemap_elements:
            # This is a sitemap index, fetch each sitemap
            for sitemap_elem in sitemap_elements:
                sitemap_loc = sitemap_elem.text
                urls.extend(parse_sitemap(sitemap_loc))
        else:
            # This is a regular sitemap
            url_elements = root.xpath('.//sm:url/sm:loc', namespaces=namespaces)
            urls = [url.text for url in url_elements if url.text]
        
        return urls
    
    except Exception as e:
        raise Exception(f"Error parsing sitemap: {str(e)}")

def check_akamai_cache(url, test_for_aem=False) -> Dict:
    """
    Check a single URL for Akamai cache status
    Returns dict with URL, cache status, and headers
    """
    try:
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=15, allow_redirects=True)
        
        # Extract Akamai headers
        x_cache = response.headers.get('X-Cache', 'NOT_FOUND')
        x_cache_remote = response.headers.get('X-Cache-Remote', 'NOT_FOUND')
        x_check_cacheable = response.headers.get('X-Check-Cacheable', 'UNKNOWN')
        x_cache_key = response.headers.get('X-Cache-Key', 'NOT_FOUND')
        x_true_cache_key = response.headers.get('X-True-Cache-Key', 'NOT_FOUND')

        # Additional cache indicators
        x_served_by = response.headers.get('X-Served-By', 'NOT_FOUND')
        x_timer = response.headers.get('X-Timer', 'NOT_FOUND')
        age = response.headers.get('Age', '0')
        cache_control = response.headers.get('Cache-Control', 'NOT_FOUND')

        # Determine cache hit status
        cache_hit = 'UNKNOWN'
        response_time_ms = None

        # Method 1: Use X-Cache if available (most accurate)
        if 'TCP_HIT' in x_cache or 'TCP_MEM_HIT' in x_cache:
            cache_hit = 'HIT'
        elif 'TCP_MISS' in x_cache:
            cache_hit = 'MISS'
        elif 'TCP_REFRESH_HIT' in x_cache:
            cache_hit = 'REFRESH_HIT'
        elif 'TCP_REFRESH_MISS' in x_cache:
            cache_hit = 'REFRESH_MISS'
        elif x_check_cacheable == 'NO':
            cache_hit = 'NOT_CACHEABLE'

        # Method 2: Use Age header (if > 0, it's cached)
        elif age and age != '0':
            cache_hit = 'HIT'

        # Method 3: Use X-Timer (Fastly/Akamai timing header)
        # Format: S<start>,VS<hit>,VS<fetch>,VE<elapsed_ms>
        elif x_timer != 'NOT_FOUND' and 'VE' in x_timer:
            try:
                # Extract VE (elapsed time in milliseconds)
                ve_part = x_timer.split('VE')[1].split(',')[0]
                response_time_ms = int(ve_part)

                # Heuristic: < 100ms is likely a cache hit, > 500ms likely miss
                if response_time_ms < 100:
                    cache_hit = 'HIT (inferred from timing)'
                elif response_time_ms > 500:
                    cache_hit = 'MISS (inferred from timing)'
                else:
                    cache_hit = 'UNKNOWN (timing inconclusive)'
            except (ValueError, IndexError):
                pass

        # Check for AEM if requested
        is_aem = None
        confidence = None
        evidence = None
        if test_for_aem:
            is_aem, confidence, evidence = detect_aem(response)

        return {
            'url': url,
            'status_code': response.status_code,
            'cache_hit': cache_hit,
            'x_cache': x_cache,
            'x_cache_remote': x_cache_remote,
            'x_check_cacheable': x_check_cacheable,
            'x_cache_key': x_cache_key,
            'x_true_cache_key': x_true_cache_key,
            'x_served_by': x_served_by,
            'x_timer': x_timer,
            'age': age,
            'cache_control': cache_control,
            'response_time_ms': response_time_ms,
            'is_aem': is_aem if test_for_aem else None,
            'aem_confidence': confidence if test_for_aem else None,
            'aem_evidence': evidence if test_for_aem else None,
            'error': None
        }
    
    except Exception as e:
        return {
            'url': url,
            'status_code': 'ERROR',
            'cache_hit': 'ERROR',
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
            'is_aem': None,
            'aem_confidence': None,
            'aem_evidence': None,
            'error': str(e)
        }

def detect_aem(response) -> Tuple[bool, float, Dict[str, list]]:
    """
    Detects if a webpage is running on Adobe Experience Manager (AEM).
    
    Args:
        response: A requests.Response object or similar with .text, .headers, and .url attributes
        
    Returns:
        Tuple of (is_aem: bool, confidence: float, evidence: dict)
        - is_aem: True if AEM is detected with confidence >= 0.3
        - confidence: Float between 0.0 and 1.0 indicating detection confidence
        - evidence: Dictionary containing lists of found indicators by category
    """
    
    confidence = 0.0
    evidence = {
        'html_classes': [],
        'data_attributes': [],
        'html_comments': [],
        'headers': [],
        'javascript_paths': [],
        'css_paths': [],
        'url_patterns': [],
        'meta_tags': []
    }
    
    html_content = response.text.lower()
    original_html = response.text  # Keep original case for evidence
    headers = {k.lower(): v for k, v in response.headers.items()}
    url = response.url
    
    # Check HTML classes (High confidence indicators)
    cq_classes = re.findall(r'class=["\'][^"\']*\b(cq-[a-z\-]+)\b[^"\']*["\']', html_content)
    if cq_classes:
        evidence['html_classes'].extend(list(set(cq_classes)))
        confidence += 0.25
    
    aem_classes = re.findall(r'class=["\'][^"\']*\b(aem-[a-z\-]+)\b[^"\']*["\']', html_content)
    if aem_classes:
        evidence['html_classes'].extend(list(set(aem_classes)))
        confidence += 0.25
    
    # Check data attributes (High confidence)
    data_attrs = re.findall(r'(data-cq-[a-z\-]+)=', html_content)
    if data_attrs:
        evidence['data_attributes'].extend(list(set(data_attrs)))
        confidence += 0.3
    
    data_path = re.search(r'data-path=["\'][^"\']*["\']', html_content)
    if data_path:
        evidence['data_attributes'].append('data-path')
        confidence += 0.15
    
    # Check HTML comments (Medium-High confidence)
    aem_comments = re.findall(r'<!--.*?(adobe experience manager|day cq|/apps/|/libs/|/content/).*?-->', 
                              html_content, re.DOTALL | re.IGNORECASE)
    if aem_comments:
        evidence['html_comments'].append(f'Found {len(aem_comments)} AEM-related comments')
        confidence += 0.2
    
    # Check HTTP headers (Medium confidence)
    for header, value in headers.items():
        if any(x in header for x in ['x-aem', 'x-cq']):
            evidence['headers'].append(f'{header}: {value}')
            confidence += 0.3
        elif 'day cq' in value.lower():
            evidence['headers'].append(f'{header}: {value}')
            confidence += 0.25
    
    # Check for clientlibs paths (High confidence)
    clientlib_js = re.findall(r'(/etc\.clientlibs/[^"\']+\.js)', html_content)
    if clientlib_js:
        evidence['javascript_paths'].extend(list(set(clientlib_js[:3])))  # Limit to 3 examples
        confidence += 0.35
    
    old_clientlib_js = re.findall(r'(/etc/clientlibs/[^"\']+\.js)', html_content)
    if old_clientlib_js:
        evidence['javascript_paths'].extend(list(set(old_clientlib_js[:3])))
        confidence += 0.35
    
    # Check for clientlibs CSS
    clientlib_css = re.findall(r'(/etc\.clientlibs/[^"\']+\.css)', html_content)
    if clientlib_css:
        evidence['css_paths'].extend(list(set(clientlib_css[:3])))
        confidence += 0.3
    
    old_clientlib_css = re.findall(r'(/etc/clientlibs/[^"\']+\.css)', html_content)
    if old_clientlib_css:
        evidence['css_paths'].extend(list(set(old_clientlib_css[:3])))
        confidence += 0.3
    
    # Check for specific AEM JavaScript libraries
    if re.search(r'(granite\.js|coral\.js|graniteui)', html_content):
        evidence['javascript_paths'].append('AEM UI frameworks (granite.js/coral.js)')
        confidence += 0.25
    
    # Check for /libs/ and /apps/ paths
    libs_paths = re.findall(r'(/libs/[^"\']+)', html_content)
    if libs_paths:
        evidence['javascript_paths'].extend(list(set(libs_paths[:2])))
        confidence += 0.2
    
    apps_paths = re.findall(r'(/apps/[^"\']+)', html_content)
    if apps_paths:
        evidence['javascript_paths'].extend(list(set(apps_paths[:2])))
        confidence += 0.2
    
    # Check URL patterns
    if '/content/' in url:
        evidence['url_patterns'].append('/content/ in URL')
        confidence += 0.15
    
    if re.search(r'\.html(\?|$)', url):
        evidence['url_patterns'].append('.html extension')
        confidence += 0.05
    
    # Check for selectors in URL (e.g., page.selector.html)
    if re.search(r'\.[a-z]+\.[a-z]+\.html', url):
        evidence['url_patterns'].append('Selector pattern in URL')
        confidence += 0.1
    
    # Check meta tags
    meta_generator = re.search(r'<meta[^>]+name=["\']generator["\'][^>]+content=["\']([^"\']+)["\']', 
                               html_content, re.IGNORECASE)
    if meta_generator and ('aem' in meta_generator.group(1).lower() or 'day cq' in meta_generator.group(1).lower()):
        evidence['meta_tags'].append(f'Generator: {meta_generator.group(1)}')
        confidence += 0.3
    
    # Check for wcmmode parameter/classes
    if re.search(r'wcmmode', html_content):
        evidence['html_classes'].append('wcmmode present')
        confidence += 0.15
    
    # Cap confidence at 1.0
    confidence = min(confidence, 1.0)
    
    # Determine if AEM is detected (threshold of 0.3)
    is_aem = confidence >= 0.3
    
    # Clean up evidence - remove empty categories
    evidence = {k: v for k, v in evidence.items() if v}
    
    return is_aem, confidence, evidence


@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')


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
    data = request.get_json()
    sitemap_url = data.get('sitemap_url', '').strip()
    check_aem = data.get('check_aem', True)  # Default to True (checked by default)

    if not sitemap_url:
        return jsonify({'error': 'Please provide a sitemap URL'}), 400

    try:
        # Parse sitemap
        urls = parse_sitemap(sitemap_url)

        if not urls:
            return jsonify({'error': 'No URLs found in sitemap'}), 400

        # Limit to reasonable number for demo (remove in production)
        max_urls = 100
        if len(urls) > max_urls:
            urls = urls[:max_urls]

        results = []

        # Split URLs into batches
        for i in range(0, len(urls), URL_BATCH_SIZE):
            batch = urls[i:i + URL_BATCH_SIZE]

            # Process current batch concurrently
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_url = {executor.submit(check_akamai_cache, url, check_aem): url for url in batch}

                for future in as_completed(future_to_url):
                    result = future.result()
                    results.append(result)

            # Wait before processing next batch (unless this is the last batch)
            if i + URL_BATCH_SIZE < len(urls):
                time.sleep(BATCH_DELAY)
        
        # Calculate statistics
        total = len(results)

        # Count hits (including inferred hits from timing)
        hits = sum(1 for r in results if 'HIT' in r['cache_hit'])

        # Count misses (including inferred misses from timing)
        misses = sum(1 for r in results if 'MISS' in r['cache_hit'])

        # Separate inferred vs confirmed for transparency
        inferred_hits = sum(1 for r in results if r['cache_hit'] == 'HIT (inferred from timing)')
        inferred_misses = sum(1 for r in results if r['cache_hit'] == 'MISS (inferred from timing)')
        confirmed_hits = sum(1 for r in results if r['cache_hit'] in ['HIT', 'REFRESH_HIT'])
        confirmed_misses = sum(1 for r in results if r['cache_hit'] in ['MISS', 'REFRESH_MISS'])

        not_cacheable = sum(1 for r in results if r['cache_hit'] == 'NOT_CACHEABLE')
        errors = sum(1 for r in results if r['cache_hit'] == 'ERROR')
        unknown = sum(1 for r in results if 'UNKNOWN' in r['cache_hit'])

        cacheable_total = total - not_cacheable - errors
        cache_hit_ratio = (hits / cacheable_total * 100) if cacheable_total > 0 else 0

        total_aem_detected = sum(1 for r in results if r.get('is_aem'))

        summary = {
            'total_urls': total,
            'cache_hits': hits,
            'cache_misses': misses,
            'confirmed_hits': confirmed_hits,
            'inferred_hits': inferred_hits,
            'confirmed_misses': confirmed_misses,
            'inferred_misses': inferred_misses,
            'not_cacheable': not_cacheable,
            'total_aem_detected': total_aem_detected,
            'errors': errors,
            'unknown': unknown,
            'cache_hit_ratio': round(cache_hit_ratio, 2)
        }
        
        return jsonify({
            'success': True,
            'summary': summary,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export', methods=['POST'])
def export_csv():
    """Export results to CSV"""
    data = request.get_json()
    results = data.get('results', [])
    
    if not results:
        return jsonify({'error': 'No results to export'}), 400
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'URL', 'Status Code', 'Cache Status', 'X-Cache',
        'X-Cache-Remote', 'X-Check-Cacheable', 'X-Cache-Key',
        'X-True-Cache-Key', 'X-Served-By', 'X-Timer', 'Age',
        'Cache-Control', 'Response Time (ms)', 'Error'
    ])

    # Write data
    for result in results:
        writer.writerow([
            result.get('url', ''),
            result.get('status_code', ''),
            result.get('cache_hit', ''),
            result.get('x_cache', ''),
            result.get('x_cache_remote', ''),
            result.get('x_check_cacheable', ''),
            result.get('x_cache_key', ''),
            result.get('x_true_cache_key', ''),
            result.get('x_served_by', ''),
            result.get('x_timer', ''),
            result.get('age', ''),
            result.get('cache_control', ''),
            result.get('response_time_ms', ''),
            result.get('error', '')
        ])
    
    # Create response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'akamai_cache_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
