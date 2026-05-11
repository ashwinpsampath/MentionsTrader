from src.client import KalshiPublicClient
from src.cache import cached
from src.markets import (
    fetch_all_open_events, filter_mention_events,
    find_mention_markets, is_tradable,
)
from src.corpus import load_corpus
from src.base_rates import compute_base_rate


client = KalshiPublicClient()
events = cached("open_events_prod", lambda: fetch_all_open_events(client))
markets = find_mention_markets(filter_mention_events(events))

mcd_markets = [
    m for m in markets
    if is_tradable(m) and m.series_ticker.startswith("KXEARNINGSMENTIONMCD")
]
print(f"Tradable MCD mention markets: {len(mcd_markets)}\n")

corpus = load_corpus()
print(len(corpus))

rows = []
for m in mcd_markets:
    phrase = m.target_phrase.split("/")[0].strip()
    # Need a small adapter — base_rates was written assuming Trump speeches.
    # We'll pass the corpus and let it count using text_by_company.
    matched = sum(
        1 for s in corpus
        if phrase.lower() in s.text_by_company().lower()
    )
    total = len(corpus)
    naive = matched / total if total else 0.0
    smoothed = (matched + 1) / (total + 2)
    midpoint = (m.yes_bid_cents + m.yes_ask_cents) // 2
    edge = int(round(smoothed * 100)) - midpoint
    rows.append((phrase, m.yes_bid_cents, m.yes_ask_cents, midpoint,
                 naive * 100, smoothed * 100, edge, matched, total, m.volume_24h))

rows.sort(key=lambda r: -abs(r[6]))

print(f"{'Phrase':<25} {'Bid':>4} {'Ask':>4} {'Mid':>4} {'Naive':>6} {'Smth':>5} {'Edge':>5} {'Hits':>6} {'Vol':>6}")
print("-" * 80)
for r in rows:
    phrase, bid, ask, mid, naive, smth, edge, matched, total, vol = r
    print(f"{phrase[:25]:<25} {bid:>4} {ask:>4} {mid:>4} {naive:>6.1f} {smth:>5.1f} {edge:>+5} {matched}/{total} {vol:>6,}")