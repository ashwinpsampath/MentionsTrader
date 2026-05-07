"""
Discovery and parsing of mention markets.

This module owns:
- Knowing what a mention market is (the heuristic)
- Fetching events from Kalshi and pulling out mention markets
- Producing clean MentionMarket objects
"""
from dataclasses import dataclass
from src.client import KalshiPublicClient


@dataclass(frozen=True)
class MentionMarket:
    """A single tradable mention market.
    
    All money in integer cents. All counts in integer contracts.
    Conversion from Kalshi's string-formatted dollar/fixed-point fields
    happens once, at parse time, in this module.
    """
    # Identity
    ticker: str
    event_ticker: str
    series_ticker: str
    
    # What we're actually trading on
    target_phrase: str           # from yes_sub_title — what word/phrase has to be said
    event_title: str             # human-readable, e.g. "What will Lyft say during their next earnings call?"
    
    # Pricing (cents, 0-100)
    yes_bid_cents: int
    yes_ask_cents: int
    no_bid_cents: int
    no_ask_cents: int
    
    # Liquidity signals
    yes_bid_size: int            # contracts available to sell into at the YES bid
    yes_ask_size: int            # contracts available to buy at the YES ask
    volume_24h: int              # contracts traded in last 24h
    open_interest: int           # contracts currently held
    
    # Timing
    close_time: str              # ISO timestamp string — when trading stops
    
    # Context for downstream LLM analysis
    rules_text: str              # rules_primary, full text
    
    # Status
    status: str                  # "active", "closed", etc.

def _dollars_str_to_cents(s: str) -> int:
    """Convert a Kalshi dollar string like '0.4800' to integer cents (48)."""
    return int(round(float(s) * 100))


def _fp_str_to_int(s: str) -> int:
    """Convert a Kalshi fixed-point string like '1233.33' to integer (1233).
    
    Truncates fractional contracts. Fractional trading produces sub-contract
    values that we don't need to trade in.
    """
    return int(float(s))

def fetch_all_open_events(client: KalshiPublicClient) -> list[dict]:
    """Pages through entire open events response and returns a single list of events"""
    all_events = []
    cursor = None
    while True:
        params = {"status": "open", "with_nested_markets": "true", "limit": 100}
        if cursor:
            params["cursor"] = cursor
        response = client.get("/events", params=params)
        all_events.extend(response["events"])
        cursor = response.get("cursor")
        if not cursor:
            break
    return all_events


def filter_mention_events(events: list[dict]) -> list[dict]:
    """
    Returns a list of only Mentions events
    """
    return [e for e in events if e["category"] == "Mentions"]

def parse_mention_market(market: dict) -> MentionMarket:
    """
    Convert a raw market dict from Kalshi's API into a MentionMarket.
    
    All string-formatted dollar and fixed-point fields are converted
    to integer cents and integer contracts respectively. 
    """
    return MentionMarket(
        ticker=market["ticker"],
        event_ticker=market["event_ticker"],
        # Series ticker is the event_ticker minus the trailing -<DATE> suffix.
        # Assumes Kalshi's convention that series names contain no hyphens.
        series_ticker=market["event_ticker"].rsplit("-", 1)[0],
        target_phrase=market["yes_sub_title"],
        event_title=market["title"],
        yes_bid_cents=_dollars_str_to_cents(market["yes_bid_dollars"]),
        yes_ask_cents=_dollars_str_to_cents(market["yes_ask_dollars"]),
        no_bid_cents=_dollars_str_to_cents(market["no_bid_dollars"]),
        no_ask_cents=_dollars_str_to_cents(market["no_ask_dollars"]),
        yes_bid_size=_fp_str_to_int(market["yes_bid_size_fp"]),
        yes_ask_size=_fp_str_to_int(market["yes_ask_size_fp"]),
        volume_24h=_fp_str_to_int(market["volume_24h_fp"]),
        open_interest=_fp_str_to_int(market["open_interest_fp"]),
        close_time=market["close_time"],
        rules_text=market["rules_primary"],
        status=market["status"],
    )
    

def find_mention_markets(events: list[dict]) -> list[MentionMarket]:
    """Given a list of events, return all parsed mention markets within them."""
    mention_markets = []
    for event in events:
        for market in event.get("markets",[]):
            mention_markets.append(parse_mention_market(market))
    return mention_markets
