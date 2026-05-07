"""
HTTP client for the Kalshi API.

This module owns:
- Loading config from environment
- Constructing full URLs from paths
- Attaching auth headers (via auth.py)
- Sending requests and parsing JSON responses

"""
import os
import requests
from dotenv import load_dotenv
from urllib.parse import urlsplit
from src.auth import build_auth_headers, load_private_key


# Load .env file once at module import time.
# This populates os.environ with the values from .env.
load_dotenv()

def _get(base_url: str, path: str, headers: dict, params: dict | None) -> dict:
    """Pure HTTP helper. No auth knowledge, no URL knowledge beyond what's passed in."""
    response = requests.get(base_url + path, headers=headers, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


class KalshiPublicClient:
    """Unauthenticated reads against production."""
    def __init__(self):
        self.base_url = os.environ["KALSHI_PUBLIC_API_BASE"]
    
    def get(self, path: str, params: dict | None = None) -> dict:
        return _get(self.base_url, path, headers={}, params=params)


class KalshiClient:
    """Authenticated client for demo (or eventually prod) trading."""
    def __init__(self):
        self.api_key_id = os.environ["KALSHI_API_KEY_ID"]
        self.private_key = load_private_key(os.environ["KALSHI_PRIVATE_KEY_PATH"])
        self.base_url = os.environ["KALSHI_API_BASE"]
    
    def get(self, path: str, params: dict | None = None) -> dict:
        signed_path = urlsplit(self.base_url).path + path
        headers = build_auth_headers(
            self.private_key, self.api_key_id, "GET", signed_path
        )
        return _get(self.base_url, path, headers=headers, params=params)
