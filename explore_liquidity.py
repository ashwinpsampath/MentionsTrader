"""Look at the distribution of liquidity signals across all mention markets.
Helps us pick reasonable thresholds for the filter."""
from src.client import KalshiPublicClient
from src.cache import cached
from src.markets import fetch_all_open_events, filter_mention_events, find_mention_markets


client = KalshiPublicClient()
events = cached("open_events_prod", lambda: fetch_all_open_events(client))
mention_events = filter_mention_events(events)
markets = find_mention_markets(mention_events)

print(f"Total mention markets: {len(markets)}\n")

# Volume distribution
volumes = sorted([m.volume_24h for m in markets])
print("=== 24h Volume distribution ===")
print(f"  min:    {volumes[0]}")
print(f"  10th %: {volumes[len(volumes) // 10]}")
print(f"  25th %: {volumes[len(volumes) // 4]}")
print(f"  median: {volumes[len(volumes) // 2]}")
print(f"  75th %: {volumes[3 * len(volumes) // 4]}")
print(f"  90th %: {volumes[9 * len(volumes) // 10]}")
print(f"  max:    {volumes[-1]}")

# Spread distribution (in cents)
spreads = sorted([m.yes_ask_cents - m.yes_bid_cents for m in markets])
print("\n=== Yes bid-ask spread distribution (cents) ===")
print(f"  min:    {spreads[0]}")
print(f"  10th %: {spreads[len(spreads) // 10]}")
print(f"  25th %: {spreads[len(spreads) // 4]}")
print(f"  median: {spreads[len(spreads) // 2]}")
print(f"  75th %: {spreads[3 * len(spreads) // 4]}")
print(f"  90th %: {spreads[9 * len(spreads) // 10]}")
print(f"  max:    {spreads[-1]}")

# Depth distribution (smaller of bid/ask size — limits us in either direction)
depths = sorted([min(m.yes_bid_size, m.yes_ask_size) for m in markets])
print("\n=== Min depth (smaller of yes_bid_size, yes_ask_size) ===")
print(f"  min:    {depths[0]}")
print(f"  10th %: {depths[len(depths) // 10]}")
print(f"  25th %: {depths[len(depths) // 4]}")
print(f"  median: {depths[len(depths) // 2]}")
print(f"  75th %: {depths[3 * len(depths) // 4]}")
print(f"  90th %: {depths[9 * len(depths) // 10]}")
print(f"  max:    {depths[-1]}")

from src.markets import is_tradable

tradable = [m for m in markets if is_tradable(m)]
print(f"\n=== After tradability filter ===")
print(f"Markets remaining: {len(tradable)} / {len(markets)} ({100*len(tradable)//len(markets)}%)")

# Show a few examples
print("\nSample tradable markets:")
for m in sorted(tradable, key=lambda x: -x.volume_24h)[:10]:
    spread = m.yes_ask_cents - m.yes_bid_cents
    print(f"  {m.ticker}: '{m.target_phrase}'")
    print(f"    yes_ask={m.yes_ask_cents}¢, spread={spread}¢, vol_24h={m.volume_24h}, depth={min(m.yes_bid_size, m.yes_ask_size)}")