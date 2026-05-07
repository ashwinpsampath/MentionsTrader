"""
Discovery and parsing of mention markets.

This module owns:
- Knowing what a mention market is (the heuristic)
- Fetching events from Kalshi and pulling out mention markets
- Producing clean MentionMarket objects
"""
from dataclasses import dataclass

from src.client import KalshiClient


@dataclass(frozen=True)
class MentionMarket:
    """A single mention market we might trade on."""
    ticker: str
    event_ticker: str
    event_title: str
    rules_text: str
    yes_ask_cents: int
    no_ask_cents: int
    volume: int
    close_time: str


def fetch_all_open_events(client: KalshiClient) -> list[dict]:
    """
    Fetch every open event from Kalshi, paginating through cursors.
    Returns raw event dicts (with nested markets).

    We return raw dicts here, not parsed objects, because:
    1. This function's job is just "get the data"
    2. Parsing is a separate concern (next function)
    3. Keeping concerns split means we can test pagination separately

    Args:
        client: An authenticated KalshiClient.

    Returns:
        A list of all open events with nested markets.
    """
    # YOUR CODE HERE
    # Pseudocode:
    #   all_events = []
    #   cursor = None
    #   while True:
    #       params = {"status": "open", "with_nested_markets": "true", "limit": 100}
    #       if cursor:
    #           params["cursor"] = cursor
    #       response = client.get("/events", params=params)
    #       all_events.extend(response["events"])
    #       cursor = response.get("cursor")
    #       if not cursor:  # no more pages
    #           break
    #   return all_events
    pass