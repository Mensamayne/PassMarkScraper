"""Analyze PassMark page structure to see what data is available."""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re


def analyze_component_page(url: str) -> dict:
    """
    Analyze a PassMark component page to see what data is available.
    
    Returns dict with all found data fields.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract all possible data
            data = {}
            
            # Component name
            title = soup.find('title')
            if title:
                data['page_title'] = title.get_text(strip=True)
            
            # All text content
            text = soup.get_text()
            
            # Look for various metrics
            metrics = {
                'CPU Mark': r'CPU Mark[:\s]+([0-9,]+)',
                'Single Thread Rating': r'Single Thread Rating[:\s]+([0-9,]+)',
                'Thread Rating': r'Thread Rating[:\s]+([0-9,]+)',
                'G3D Mark': r'G3D Mark[:\s]+([0-9,]+)',
                'G2D Mark': r'G2D Mark[:\s]+([0-9,]+)',
                'TDP': r'TDP[:\s]+([0-9]+)\s*W',
                'Price': r'Price[:\s]*\$([0-9,.]+)',
                'Cores': r'(\d+)\s*Cores?',
                'Threads': r'(\d+)\s*Threads?',
                'Base Clock': r'Base Clock[:\s]+([0-9.]+)\s*GHz',
                'Boost Clock': r'Boost(?:\s+Clock)?[:\s]+([0-9.]+)\s*GHz',
                'Socket': r'Socket[:\s]+([A-Z0-9-]+)',
                'Memory Size': r'(\d+)\s*GB',
                'Memory Type': r'(DDR[345])',
                'Release Date': r'Release Date[:\s]+([A-Za-z]+\s+\d{4})',
                'Launch Date': r'Launch Date[:\s]+([A-Za-z]+\s+\d{4})',
                'Architecture': r'Architecture[:\s]+([A-Za-z0-9\s]+)',
                'Process': r'(\d+)\s*nm',
                'Cache': r'Cache[:\s]+([0-9.]+)\s*MB',
                'L3 Cache': r'L3 Cache[:\s]+([0-9.]+)\s*MB',
            }
            
            data['found_metrics'] = {}
            for metric_name, pattern in metrics.items():
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    data['found_metrics'][metric_name] = match.group(1)
            
            # Find all tables
            tables = soup.find_all('table')
            data['table_count'] = len(tables)
            
            # Find all list items
            lists = soup.find_all(['ul', 'ol'])
            data['list_count'] = len(lists)
            
            # Find all divs with class containing 'spec' or 'info'
            spec_divs = soup.find_all('div', class_=re.compile(r'(spec|info|detail)', re.IGNORECASE))
            data['spec_div_count'] = len(spec_divs)
            
            # Sample some content
            if spec_divs:
                data['sample_spec_divs'] = []
                for div in spec_divs[:3]:
                    data['sample_spec_divs'].append({
                        'class': div.get('class'),
                        'text': div.get_text(strip=True)[:200]
                    })
            
            return data
            
        finally:
            browser.close()

