"""Web scraper for PassMark benchmarks."""
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re


def scrape_single_component(url: str) -> dict:
    """
    Scrape a single component from PassMark.
    
    Args:
        url: PassMark URL
    
    Returns:
        dict with keys: name, passmark_score, component_type, tdp (optional)
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to URL
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            
            # Wait for content to load
            page.wait_for_timeout(2000)
            
            # Get page content
            html = page.content()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Determine component type from URL
            if "cpubenchmark.net" in url:
                component_type = "CPU"
            elif "videocardbenchmark.net" in url:
                component_type = "GPU"
            elif "memorybenchmark.net" in url or "rambenchmark" in url:
                component_type = "RAM"
            elif "harddrivebenchmark.net" in url or "diskbenchmark" in url:
                component_type = "STORAGE"
            else:
                component_type = "UNKNOWN"
            
            # Extract component name
            name = extract_component_name(soup, url)
            
            # Extract PassMark score
            score = extract_passmark_score(soup, component_type)
            
            # Extract all additional specs
            text = soup.get_text()
            
            result = {
                "name": name,
                "passmark_score": score,
                "component_type": component_type,
            }
            
            # Extract comprehensive specs based on type
            if component_type == "CPU":
                result.update(extract_cpu_specs(soup, text))
            elif component_type == "GPU":
                result.update(extract_gpu_specs(soup, text))
            elif component_type == "RAM":
                result.update(extract_ram_specs(soup, text))
            elif component_type == "STORAGE":
                result.update(extract_storage_specs(soup, text))
            
            return result
            
        finally:
            browser.close()


def extract_component_name(soup: BeautifulSoup, url: str) -> str:
    """Extract component name from page."""
    # Strategy 1: Try to extract from URL parameters
    param_patterns = [
        r'cpu=([^&]+)',
        r'gpu=([^&]+)',
        r'ram=([^&]+)',
        r'hdd=([^&]+)',
        r'memory=([^&]+)',
        r'drive=([^&]+)',
    ]
    
    for pattern in param_patterns:
        match = re.search(pattern, url)
        if match:
            name = match.group(1).replace('+', ' ')
            # URL decode
            name = name.replace('%20', ' ')
            # Clean up
            name = re.sub(r'\s+', ' ', name).strip()
            if name and len(name) > 3:
                return name
    
    # Strategy 2: Try common selectors for component name
    selectors = [
        ('span', {'class': 'cpuname'}),
        ('div', {'class': 'cpuname'}),
        ('div', {'class': 'left-desc-cpu'}),
        ('h1', {}),
        ('span', {'class': 'fontblack'}),
    ]
    
    for tag, attrs in selectors:
        element = soup.find(tag, attrs)
        if element:
            name = element.get_text(strip=True)
            # Clean up name
            name = re.sub(r'\s+', ' ', name)
            # Validate it's not a generic title
            if name and len(name) > 3 and not any(x in name.lower() for x in ['benchmark', 'list', 'chart', 'rating']):
                return name
    
    # Strategy 3: Look for title tag
    title = soup.find('title')
    if title:
        title_text = title.get_text(strip=True)
        # Remove common suffixes
        title_text = re.sub(r'\s*-\s*(PassMark|CPU|GPU|Benchmarks?).*', '', title_text, flags=re.IGNORECASE)
        title_text = re.sub(r'\s+', ' ', title_text).strip()
        if title_text and len(title_text) > 3:
            return title_text
    
    raise ValueError("Could not extract component name from page")


def extract_passmark_score(soup: BeautifulSoup, component_type: str) -> int:
    """Extract PassMark score from page."""
    text = soup.get_text()
    
    # Define patterns for each component type
    patterns = []
    
    if component_type == "CPU":
        patterns = [
            r'CPU Mark[:\s]+([0-9,]+)',
            r'PassMark[:\s]+([0-9,]+)',
            r'Rating[:\s]+([0-9,]+)',
        ]
    elif component_type == "GPU":
        patterns = [
            r'G3D Mark[:\s]+([0-9,]+)',
            r'VideoCard Mark[:\s]+([0-9,]+)',
            r'Graphics Mark[:\s]+([0-9,]+)',
        ]
    elif component_type == "RAM":
        patterns = [
            r'Average Mark[:\s]+([0-9,]+)',
            r'Memory Mark[:\s]+([0-9,]+)',
            r'RAM Mark[:\s]+([0-9,]+)',
            r'PassMark[:\s]+([0-9,]+)',
        ]
    elif component_type == "STORAGE":
        patterns = [
            r'Disk Mark[:\s]+([0-9,]+)',
            r'Drive Mark[:\s]+([0-9,]+)',
        ]
    
    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score_str = match.group(1).replace(',', '')
            try:
                score = int(score_str)
                # Sanity check: score should be reasonable
                if 100 <= score <= 100000:
                    return score
            except ValueError:
                continue
    
    # Strategy 2: Look in specific HTML elements
    score_elements = soup.find_all(['span', 'strong', 'div'], class_=re.compile(r'(mark|score|rating)', re.IGNORECASE))
    for elem in score_elements:
        text_content = elem.get_text(strip=True)
        numbers = re.findall(r'\b([0-9,]{4,})\b', text_content)
        for num_str in numbers:
            try:
                score = int(num_str.replace(',', ''))
                if 100 <= score <= 100000:
                    return score
            except ValueError:
                continue
    
    # Fallback: look for numbers in specific ranges
    numbers = re.findall(r'\b([0-9]{4,6})\b', text)
    if numbers:
        # Filter to reasonable score ranges
        valid_scores = []
        for num_str in numbers:
            try:
                num = int(num_str)
                if 500 <= num <= 50000:  # Typical PassMark range
                    valid_scores.append(num)
            except ValueError:
                continue
        
        if valid_scores:
            # Return the most likely score (usually one of the larger ones)
            return sorted(valid_scores, reverse=True)[0]
    
    raise ValueError(f"Could not extract PassMark score for {component_type}")


def extract_cpu_specs(soup: BeautifulSoup, text: str) -> dict:
    """Extract comprehensive CPU specifications."""
    specs = {}
    
    patterns = {
        'single_thread_rating': r'Single Thread Rating[:\s]+([0-9,]+)',
        'thread_rating': r'Thread Rating[:\s]+([0-9,]+)',
        'tdp': r'TDP[:\s]+([0-9]+)\s*W',
        'cores': r'(\d+)\s*Cores?',
        'threads': r'(\d+)\s*Threads?',
        'base_clock': r'(?:Base Clock|Base Frequency)[:\s]+([0-9.]+)\s*GHz',
        'boost_clock': r'(?:Boost|Max|Turbo)(?:\s+Clock|\s+Frequency)?[:\s]+([0-9.]+)\s*GHz',
        'socket': r'Socket[:\s]+([A-Z0-9-]+)',
        'cache': r'Cache[:\s]+([0-9.]+)\s*MB',
        'l3_cache': r'L3 Cache[:\s]+([0-9.]+)\s*MB',
        'process': r'(\d+)\s*nm',
        'architecture': r'Architecture[:\s]+([A-Za-z0-9\s]+)',
        'release_date': r'(?:Release|Launch) Date[:\s]+([A-Za-z]+\s+\d{4})',
        'price': r'Price[:\s]*\$([0-9,.]+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')
            # Try to convert to int if it's a number
            try:
                if key in ['tdp', 'cores', 'threads', 'process']:
                    specs[key] = int(value)
                elif key in ['base_clock', 'boost_clock', 'cache', 'l3_cache']:
                    specs[key] = float(value)
                elif key == 'price':
                    specs[key] = float(value)
                elif key in ['single_thread_rating', 'thread_rating']:
                    specs[key] = int(value)
                else:
                    specs[key] = value.strip()
            except ValueError:
                specs[key] = value.strip()
    
    return specs


def extract_gpu_specs(soup: BeautifulSoup, text: str) -> dict:
    """Extract comprehensive GPU specifications."""
    specs = {}
    
    patterns = {
        'g3d_mark': r'G3D Mark[:\s]+([0-9,]+)',
        'g2d_mark': r'G2D Mark[:\s]+([0-9,]+)',
        'tdp': r'TDP[:\s]+([0-9]+)\s*W',
        'memory_size': r'(?:Memory Size|VRAM)[:\s]+([0-9]+)\s*GB',
        'memory_type': r'(GDDR[56X]|DDR[345]|HBM[23]?)',
        'memory_bus': r'(?:Bus Width|Memory Bus)[:\s]+([0-9]+)\s*bit',
        'memory_bandwidth': r'(?:Bandwidth|Memory Bandwidth)[:\s]+([0-9.]+)\s*GB/s',
        'cuda_cores': r'(?:CUDA Cores|Stream Processors)[:\s]+([0-9,]+)',
        'base_clock': r'Base Clock[:\s]+([0-9,]+)\s*MHz',
        'boost_clock': r'Boost Clock[:\s]+([0-9,]+)\s*MHz',
        'architecture': r'Architecture[:\s]+([A-Za-z0-9\s]+)',
        'process': r'(\d+)\s*nm',
        'release_date': r'(?:Release|Launch) Date[:\s]+([A-Za-z]+\s+\d{4})',
        'price': r'Price[:\s]*\$([0-9,.]+)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')
            try:
                if key in ['tdp', 'memory_size', 'memory_bus', 'cuda_cores', 'base_clock', 'boost_clock', 'process']:
                    specs[key] = int(value)
                elif key in ['memory_bandwidth', 'price']:
                    specs[key] = float(value)
                elif key in ['g3d_mark', 'g2d_mark']:
                    specs[key] = int(value)
                else:
                    specs[key] = value.strip()
            except ValueError:
                specs[key] = value.strip()
    
    return specs


def extract_ram_specs(soup: BeautifulSoup, text: str) -> dict:
    """Extract RAM specifications."""
    specs = {}
    
    patterns = {
        'speed': r'(\d+)\s*MHz',
        'latency': r'CL(\d+)',
        'capacity': r'(\d+)\s*GB',
        'type': r'(DDR[345])',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1)
            try:
                if key in ['speed', 'latency', 'capacity']:
                    specs[key] = int(value)
                else:
                    specs[key] = value
            except ValueError:
                specs[key] = value
    
    return specs


def extract_storage_specs(soup: BeautifulSoup, text: str) -> dict:
    """Extract storage specifications."""
    specs = {}
    
    patterns = {
        'capacity': r'(\d+)\s*(?:TB|GB)',
        'interface': r'(SATA|NVMe|PCIe\s*[345]\.0)',
        'read_speed': r'Read[:\s]+([0-9,]+)\s*MB/s',
        'write_speed': r'Write[:\s]+([0-9,]+)\s*MB/s',
        'type': r'(SSD|HDD|NVMe)',
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')
            try:
                if key in ['read_speed', 'write_speed']:
                    specs[key] = int(value)
                else:
                    specs[key] = value
            except ValueError:
                specs[key] = value
    
    return specs

