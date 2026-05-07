"""
Simple disk-based cache for development.

Used to avoid re-hitting slow APIs every run while iterating on analysis logic.
NOT used by production code — the bot always wants fresh data.

Usage:
    events = cached("open_events", lambda: fetch_all_open_events(client))

First call: invokes fetch_all_open_events(), saves result to .cache/open_events.json
Subsequent calls: reads from disk instantly.

To force a refresh: delete the .cache/ directory, or pass force_refresh=True.
"""
import json
from pathlib import Path
from typing import Callable, Any

CACHE_DIR = Path(".cache")


def cached(name: str, fetch_fn: Callable[[], Any], *, force_refresh: bool = False) -> Any:
    """
    Get a value from disk cache, or compute and cache it if missing.

    Args:
        name: Cache filename (without extension). Use snake_case.
        fetch_fn: Zero-argument function that produces the value on cache miss.
        force_refresh: If True, ignore existing cache and re-fetch.

    Returns:
        The cached value, parsed from JSON.
    """
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / f"{name}.json"

    if cache_file.exists() and not force_refresh:
        return json.loads(cache_file.read_text())

    value = fetch_fn()
    cache_file.write_text(json.dumps(value, indent=2))
    return value