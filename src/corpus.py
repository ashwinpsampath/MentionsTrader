"""
Curated corpus of Trump speech transcripts from Rev.

Each entry: (url, iso_date, event_type)
event_type values: rally, speech, announcement, interview, ceremony

Hand-picked for Trump-dominant content.
"""

from src.fetcher import fetch_html
from src.speeches import Speech, build_speech_from_motley_fool

"""
Curated corpus of McDonald's earnings call transcripts from Motley Fool.

Each entry: (url, iso_date, ticker)

This is the v1 corpus. 4 calls is small but enough to validate the pipeline
end-to-end before scaling. After this works, extend by:
  - Adding more past quarters for McDonald's (try Q1 2025 via Motley Fool search
    or fall back to mlq.ai / GuruFocus if fool.com doesn't have it)
  - Adding other companies (Lyft, Airbnb) — same Motley Fool URL pattern
"""

EARNINGS_CALLS: list[tuple[str, str, str]] = [
    # Q1 2026 — most recent, full call already validated end-to-end
    (
        "https://www.fool.com/earnings/call-transcripts/2026/02/23/hims-hers-hims-earnings-call-transcript/",
        "2026-02-23",
        "HIMS",
    ),
    # Q4 2025 — published Feb 11, 2026
    (
        "https://www.fool.com/earnings/call-transcripts/2025/11/03/hims-hers-hims-q3-2025-earnings-call-transcript/",
        "2025-11-03",
        "HIMS",
    )
]

def load_corpus() -> list[Speech]:
    """Fetch (or load from cache) and parse the entire speech corpus.
    
    Skips entries that fail to fetch.
    
    Returns:
        A list of Speech objects, one per successfully-loaded transcript.
    """
    corpus = []
    for url, date, ticker in EARNINGS_CALLS:
        html = fetch_html(url)
        if html is None:
            print(f"  skipped (fetch failed): {url}")
            continue
        
        try:
            speech = build_speech_from_motley_fool(url, date, ticker, html)
        except Exception as e:
            # If parsing fails on one transcript, skip it but don't crash
            print(f"  skipped (parse failed): {url} — {type(e).__name__}: {e}")
            continue
        
        corpus.append(speech)
    
    return corpus