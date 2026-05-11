from src.client import KalshiPublicClient
from src.cache import cached
from src.markets import (
    fetch_all_open_events, filter_mention_events,
    find_mention_markets, is_tradable,
)
from src.corpus import load_corpus


client = KalshiPublicClient()
events = cached("open_events_prod", lambda: fetch_all_open_events(client))
markets = find_mention_markets(filter_mention_events(events))

hims_markets = [
    m for m in markets
    if is_tradable(m) and m.series_ticker.startswith("KXEARNINGSMENTIONHIMS")
]
print(f"Tradable HIMS mention markets: {len(hims_markets)}\n")

corpus = load_corpus()
print(f"Corpus: {len(corpus)} calls\n")

rows = []
for m in hims_markets:
    phrase = m.target_phrase.split("/")[0].strip()
    matched = sum(
        1 for s in corpus
        if phrase.lower() in s.text_by_company().lower()
    )
    total = len(corpus)
    smoothed = (matched + 1) / (total + 2)
    midpoint = (m.yes_bid_cents + m.yes_ask_cents) // 2
    edge = int(round(smoothed * 100)) - midpoint
    rows.append((phrase, m.yes_bid_cents, m.yes_ask_cents,
                 midpoint, matched * 100 / total, smoothed * 100,
                 edge, matched, total, m.volume_24h))

rows.sort(key=lambda r: -abs(r[6]))

print(f"{'Phrase':<25} {'Bid':>4} {'Ask':>4} {'Mid':>4} {'Naive':>6} {'Smth':>5} {'Edge':>5} {'Hits':>5} {'Vol':>6}")
print("-" * 85)
for r in rows:
    phrase, bid, ask, mid, naive, smth, edge, matched, total, vol = r
    print(f"{phrase[:25]:<25} {bid:>4} {ask:>4} {mid:>4} "
          f"{naive:>6.1f} {smth:>5.1f} {edge:>+5} "
          f"{matched}/{total} {vol:>6,}")