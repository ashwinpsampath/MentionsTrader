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

class KalshiClient:
    """
    Minimal authenticated HTTP client for the Kalshi API.

    Usage:
        client = KalshiClient()
        balance = client.get("/portfolio/balance")
    """

    def __init__(self):
        # Read config from environment — set in .env
        # KeyError is raised if any keys are missing
        self.api_key_id = os.environ["KALSHI_API_KEY_ID"]
        self.private_key = load_private_key(os.environ["KALSHI_PRIVATE_KEY_PATH"])
        self.base_url = os.environ["KALSHI_API_BASE"]

    def get(self, path: str, params: dict | None = None) -> dict:
        """
        Make an authenticated GET request to Kalshi.
        """
        url = self.base_url + path
        path_prefix = urlsplit(self.base_url).path
        signed_path = path_prefix + path
        headers = build_auth_headers(self.private_key,self.api_key_id, "GET", signed_path)
        response = requests.get(url,headers=headers,params=params, timeout=10)
        response.raise_for_status()
        return response.json()
