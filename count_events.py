from src.client import KalshiPublicClient
from src.cache import cached
from src.markets import fetch_all_open_events, filter_mention_events, find_mention_markets

client = KalshiPublicClient()

events = cached("open_events_prod", lambda: fetch_all_open_events(client))
mention_events = filter_mention_events(events)

print(f"Total open events: {len(events)}")
print(f"Mention events: {len(mention_events)}")

total_markets = sum(len(e.get("markets", [])) for e in mention_events)
print(f"Total mention markets across those events: {total_markets}")

markets = find_mention_markets(mention_events)
print(f"\nParsed {len(markets)} mention markets")
print("\n--- Sample parsed markets ---")
for m in markets[:5]:
    print(m)
