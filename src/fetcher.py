"""
Polite, caching HTTP fetcher for transcript pages.

Owns:
- Network requests with identifying User-Agent
- Disk caching of raw HTML
- Rate limiting between fetches
- Graceful handling of 4xx/5xx responses
"""
import hashlib
import time
import requests
from pathlib import Path
from bs4 import BeautifulSoup


CACHE_DIR = Path(".cache/html")
USER_AGENT = "kalshi-mention-bot/0.1 (personal research; learning project)"
REQUEST_TIMEOUT = 15  # seconds
RATE_LIMIT_SECONDS = 2  # minimum delay between actual network fetches


# Module-level state to track when we last hit the network.
# Used to enforce the rate limit across multiple fetches in one session.
_last_fetch_time: float = 0.0


def _url_to_cache_path(url: str) -> Path:
    """Convert a URL to a deterministic cache file path.
    
    We hash the URL because URLs can contain characters that aren't
    valid in filenames (slashes, query strings, etc.), and hashing
    sidesteps all of that. The first 16 hex chars give us 2^64
    possibilities, which is overkill for our 15-URL corpus but
    cheap insurance against collisions.
    """
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:16]
    return CACHE_DIR / f"{digest}.html"


def fetch_html(url: str, *, force_refresh: bool = False) -> str | None:
    """Fetch the HTML content of a URL, with disk caching and polite behaviors.
    
    Args:
        url: The URL to fetch. Must include scheme (http:// or https://).
        force_refresh: If True, bypass the cache and re-fetch from network.
    
    Returns:
        The HTML content as a string, or None if the fetch failed
        (404, 5xx, network error, etc.).
    
    Side effects:
        - Caches successful responses to disk
        - Sleeps to maintain rate limit between network fetches
        - Prints a status line for each fetch (cached vs. network)
    """
    global _last_fetch_time
    
    cache_file = _url_to_cache_path(url)
    
    # Check cache first
    if cache_file.exists() and not force_refresh:
        print(f"[cached] {url}")
        return cache_file.read_text(encoding="utf-8")
    
    # Rate limit: ensure at least RATE_LIMIT_SECONDS since last network fetch
    elapsed = time.time() - _last_fetch_time
    if elapsed < RATE_LIMIT_SECONDS:
        sleep_for = RATE_LIMIT_SECONDS - elapsed
        time.sleep(sleep_for)
    
    print(f"[fetching] {url}")
    
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=REQUEST_TIMEOUT,
        )
        _last_fetch_time = time.time()
        
        if response.status_code != 200:
            print(f"  failed: HTTP {response.status_code}")
            return None
        
        # Cache the successful response
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(response.text, encoding="utf-8")
        return response.text
    
    except requests.RequestException as e:
        # Catches timeouts, connection errors, DNS failures, etc.
        _last_fetch_time = time.time()
        print(f"  failed: {type(e).__name__}: {e}")
        return None

def html_to_text(html: str) -> str:
    """
    Convert HTML to clean plain text suitable for transcript parsing.
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "header", "footer"]):
        tag.decompose()
    
    paragraphs = soup.find_all("p")
    return "\n".join(
        p.get_text(separator=" ", strip=True)
        for p in paragraphs
    )