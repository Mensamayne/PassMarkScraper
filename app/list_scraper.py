"""Scraper for PassMark ranking lists."""

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import re
import logging
from app.config_loader import config

logger = logging.getLogger(__name__)


def scrape_top_components(
    component_type: str, limit: int = 10, max_attempts: int = None
) -> list[dict]:
    """
    Scrape top components from PassMark ranking lists.

    Args:
        component_type: "CPU" | "GPU" | "RAM" | "STORAGE"
        limit: Number of top components to return (-1 for all available)
        max_attempts: Maximum number of items to attempt scraping (prevents infinite loops)

    Returns:
        List of dicts with: name, passmark_score, rank
    """
    # Safety: if limit is -1, set max_attempts to reasonable value
    if limit == -1:
        limit = 10000  # Very high number

    if max_attempts is None:
        max_attempts = limit * 3  # Try 3x the limit to account for parsing failures

    # Special handling for RAM - scrape all DDR types
    if component_type == "RAM":
        return scrape_all_ram_types(limit, max_attempts)

    # Determine URL based on component type and config setting
    use_full_lists = config.get_use_full_lists()

    if component_type == "CPU":
        url = (
            "https://www.cpubenchmark.net/cpu_list.php"
            if use_full_lists
            else "https://www.cpubenchmark.net/high_end_cpus.html"
        )
    elif component_type == "GPU":
        url = (
            "https://www.videocardbenchmark.net/gpu_list.php"
            if use_full_lists
            else "https://www.videocardbenchmark.net/high_end_gpus.html"
        )
    elif component_type == "STORAGE":
        url = (
            "https://www.harddrivebenchmark.net/hdd_list.php"
            if use_full_lists
            else "https://www.harddrivebenchmark.net/high_end_drives.html"
        )
    else:
        raise ValueError(f"Unknown component type: {component_type}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            # Navigate to ranking page
            page.goto(url, timeout=30000, wait_until="domcontentloaded")

            # For full lists (cpu_list.php, gpu_list.php), wait longer for JavaScript data to load
            if "list.php" in url:
                logger.debug(f"Waiting for JavaScript data on {url}...")
                page.wait_for_timeout(10000)  # Wait 10 seconds for JS to load data
            else:
                page.wait_for_timeout(2000)

            # Get page content
            html = page.content()
            soup = BeautifulSoup(html, "html.parser")

            # Find the ranking table
            components = []

            # PassMark uses various table formats, try multiple approaches

            # Approach 1: For full lists (cpu_list.php, gpu_list.php) - look for table with id
            table = None
            if use_full_lists:
                if component_type == "CPU":
                    table = soup.find("table", {"id": "cputable"})
                elif component_type == "GPU":
                    table = soup.find("table", {"id": "cputable"})  # GPU list also uses cputable
                elif component_type == "STORAGE":
                    table = soup.find("table", {"id": "cputable"})

            if table:
                # Parse table rows (full list format)
                rows = table.find_all("tr")[1:]  # Skip header row
                logger.debug(f"Found table with {len(rows)} rows")
            else:
                # Approach 2: Look for chart-list-item (high_end format)
                rows = soup.find_all("li", class_="chart-list-item")
                if not rows:
                    # Approach 3: Look for chart_body
                    chart_body = soup.find("ul", id="cputable")
                    if not chart_body:
                        chart_body = soup.find("ul", class_="chartlist")
                    if chart_body:
                        rows = chart_body.find_all("li")

                if not rows:
                    # Approach 4: Try parsing any table
                    table = soup.find("table")
                    if table:
                        rows = table.find_all("tr")[1:]  # Skip header

            rank = 1
            max_rows = min(len(rows), max_attempts)

            for row in rows[:max_rows]:
                if len(components) >= limit:
                    break  # Reached desired limit
                try:
                    tds = row.find_all("td")
                    name_elem = None
                    score_elem = None
                    score_str = None

                    # Strategy 1: Table rows with <td> elements
                    if tds and len(tds) >= 2:
                        # RAM has special format: [Name, Latency, Read, Write, Price]
                        if component_type == "RAM" and len(tds) >= 4 and not table:
                            name_elem = tds[0]
                            try:
                                read_speed = float(tds[2].get_text(strip=True))
                                write_speed = float(tds[3].get_text(strip=True))
                                # Calculate synthetic score from speeds
                                score_value = int((read_speed * 0.6 + write_speed * 0.4) * 300)
                                score_str = str(score_value)
                                score_elem = True  # Mark as processed
                            except (ValueError, AttributeError):
                                continue
                        # STORAGE has format: [Name, Capacity, Score, ...]
                        elif component_type == "STORAGE" and len(tds) >= 3 and table:
                            name_elem = tds[0]
                            score_elem = tds[2]  # Score is in column 2 for storage
                        else:
                            # Standard table format: [Name, Score, Rank, ...]
                            name_elem = tds[0]
                            score_elem = tds[1]

                    # Strategy 2: List items with <span> elements (high-end lists)
                    if not name_elem:
                        name_elem = row.find("span", class_="prdname")
                        if not name_elem:
                            name_elem = row.find("a")

                    if not score_elem and not score_str:
                        score_elem = row.find("span", class_="count")

                    if not score_elem:
                        # Try to find any number in the row
                        text = row.get_text()
                        score_match = re.search(r"([0-9,]{3,})", text)
                        if score_match:
                            score_str = score_match.group(1).replace(",", "")
                        else:
                            continue
                    elif score_elem is not True:  # If not already processed (RAM case)
                        score_str = score_elem.get_text(strip=True).replace(",", "")

                    if name_elem:
                        name = name_elem.get_text(strip=True)
                        # Clean up name
                        name = re.sub(r"\s+", " ", name)

                        # Skip if name is too short or contains only numbers
                        if len(name) < 3 or name.isdigit():
                            continue

                        try:
                            score = int(score_str)
                            # Sanity check: PassMark scores should be reasonable
                            if score < 1 or score > 100000000:  # Filter out model numbers
                                continue

                            components.append({"rank": rank, "name": name, "passmark_score": score})
                            rank += 1
                        except ValueError:
                            continue

                except Exception:
                    # Skip problematic rows
                    continue

            return components

        finally:
            browser.close()


def scrape_all_ram_types(limit: int = 10000, max_attempts: int = None) -> list[dict]:
    """
    Scrape all RAM types (DDR5, DDR4, DDR3, DDR2) from PassMark.

    Args:
        limit: Total number of RAM modules to return
        max_attempts: Maximum attempts per DDR type

    Returns:
        Combined list of all RAM modules
    """
    ram_urls = [
        ("DDR5", "https://www.memorybenchmark.net/ram_list.php"),
        ("DDR4", "https://www.memorybenchmark.net/ram_list-ddr4.php"),
        ("DDR3", "https://www.memorybenchmark.net/ram_list-ddr3.php"),
        ("DDR2", "https://www.memorybenchmark.net/ram_list-ddr2.php"),
    ]

    all_components = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            for ddr_type, url in ram_urls:
                logger.debug(f"Scraping {ddr_type} from {url}...")

                # Navigate to page
                page.goto(url, timeout=30000, wait_until="domcontentloaded")

                # Wait for JavaScript data to load
                if "list.php" in url or "list-" in url:
                    logger.debug(f"Waiting for JavaScript data on {url}...")
                    page.wait_for_timeout(10000)  # Wait 10 seconds
                else:
                    page.wait_for_timeout(2000)

                # Get page content
                html = page.content()
                soup = BeautifulSoup(html, "html.parser")

                # Find table
                table = soup.find("table", {"id": "cputable"})

                if not table:
                    logger.debug(f"No table found for {ddr_type}")
                    continue

                rows = table.find_all("tr")[1:]  # Skip header
                logger.debug(f"Found {len(rows)} rows for {ddr_type}")

                # Parse rows
                for row in rows:
                    if len(all_components) >= limit:
                        break

                    try:
                        tds = row.find_all("td")

                        if tds and len(tds) >= 4:
                            # RAM format: [Name, Latency, Read, Write, Price]
                            name_elem = tds[0]

                            try:
                                read_speed = float(tds[2].get_text(strip=True))
                                write_speed = float(tds[3].get_text(strip=True))

                                # Calculate synthetic score
                                score_value = int((read_speed * 0.6 + write_speed * 0.4) * 300)

                                if score_value < 1 or score_value > 100000000:
                                    continue

                                name = name_elem.get_text(strip=True)
                                name = re.sub(r"\s+", " ", name)

                                if len(name) < 3 or name.isdigit():
                                    continue

                                all_components.append(
                                    {
                                        "rank": len(all_components) + 1,
                                        "name": f"{name} ({ddr_type})",  # Add DDR type to name
                                        "passmark_score": score_value,
                                    }
                                )

                            except (ValueError, AttributeError):
                                continue

                    except Exception:
                        continue

                if len(all_components) >= limit:
                    break

            logger.info(f"Total RAM modules scraped: {len(all_components)}")
            return all_components

        finally:
            browser.close()
