"""
shopify_api.py

Shopify API module that handles REST API calls, pagination, and rate limiting.
"""

import time
import logging
import requests
from urllib.parse import urljoin
from config import BASE_URL, REQUESTS_HEADERS

logger = logging.getLogger("update_shopify_history_database_logger")

# Create a session with default headers
REQUESTS_SESSION = requests.Session()
REQUESTS_SESSION.headers.update(REQUESTS_HEADERS)


def parse_link_header(header: str):
    """Parse Link header and return a dict of rel->url"""
    links = {}
    if not header:
        return links

    parts = header.split(",")
    for p in parts:
        section = p.strip().split(";")
        if len(section) < 2:
            continue

        url_part = section[0].strip()
        rel_part = section[1].strip()

        url = url_part[url_part.find("<") + 1 : url_part.find(">")]
        rel = rel_part.split("=")[1].strip('"')

        links[rel] = url

    return links


def request_with_retries(url, params=None, method="GET", max_retries=5):
    """Fetch URL with retry logic for rate limiting"""
    sleep_seconds = 1

    for attempt in range(max_retries):
        try:
            if method == "GET":
                resp = REQUESTS_SESSION.get(url, params=params, timeout=30)
            else:
                resp = REQUESTS_SESSION.request(method, url, params=params, timeout=30)

            if resp.status_code == 429:
                # Rate limited - wait and retry
                retry_after = int(resp.headers.get("Retry-After", sleep_seconds))
                logger.warning(f"Rate limited by Shopify. Sleeping {retry_after} seconds.")
                time.sleep(retry_after)
                sleep_seconds *= 2
                continue

            resp.raise_for_status()
            return resp

        except requests.exceptions.RequestException as e:
            logger.exception(f"Request failed (attempt {attempt + 1}/{max_retries}): {e}")
            time.sleep(sleep_seconds)
            sleep_seconds *= 2

    raise RuntimeError(f"Failed to fetch url after {max_retries} attempts: {url}")


def fetch_all_rest(endpoint: str, params: dict = None, item_key: str = None):
    """Fetch all pages for a REST endpoint using pagination"""
    url = urljoin(BASE_URL, endpoint)
    params = params or {}
    params.setdefault("limit", 250)

    all_items = []
    page_count = 0

    resp = request_with_retries(url, params=params)
    page_count += 1
    data = resp.json()

    if item_key:
        items = data.get(item_key, [])
        all_items.extend(items)
    else:
        all_items.append(data)

    links = parse_link_header(resp.headers.get("Link", ""))

    while links.get("next"):
        next_url = links["next"]
        resp = request_with_retries(next_url)
        page_count += 1
        data = resp.json()

        if item_key:
            all_items.extend(data.get(item_key, []))
        else:
            all_items.append(data)

        links = parse_link_header(resp.headers.get("Link", ""))

    logger.info(f"Fetched {page_count} pages from {endpoint} (total items: {len(all_items)})")
    return all_items
