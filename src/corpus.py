"""
Curated corpus of Trump speech transcripts from Rev.

Each entry: (url, iso_date, event_type)
event_type values: rally, speech, announcement, interview, ceremony

Hand-picked for Trump-dominant content.
"""

from src.fetcher import fetch_html
from src.speeches import Speech, build_speech

TRUMP_SPEECHES: list[tuple[str, str, str]] = [
    # --- Major speeches and rallies (highest Trump-density) ---
    (
        "https://www.rev.com/transcripts/2026-state-of-the-union-address",
        "2026-02-25",
        "speech",
    ),
    (
        "https://www.rev.com/transcripts/trump-rally-in-kentucky",
        "2026-03-12",
        "rally",
    ),
    (
        "https://www.rev.com/transcripts/trump-rally-in-texas",
        "2026-03-01",
        "rally",
    ),
    (
        "https://www.rev.com/transcripts/trump-event-in-florida",
        "2026-05-04",
        "rally",
    ),
    (
        "https://www.rev.com/transcripts/trump-speaks-at-tpusa-event",
        "2026-04-20",
        "rally",
    ),
    (
        "https://www.rev.com/transcripts/trump-speaks-at-un",
        "2025-09-23",
        "speech",
    ),
    (
        "https://www.rev.com/transcripts/trump-at-navy-250th",
        "2025-10-13",
        "speech",
    ),
    (
        "https://www.rev.com/transcripts/donald-trump-west-point-commencement-speech-transcript",
        "2025-05-24",
        "speech",
    ),

    # --- Announcements and signings (Trump-dominant, shorter) ---
    (
        "https://www.rev.com/transcripts/trumprx-announcement",
        "2026-02-08",
        "announcement",
    ),
    (
        "https://www.rev.com/transcripts/oval-office-ufc-announcement",
        "2026-05-07",
        "announcement",
    ),
    (
        "https://www.rev.com/transcripts/retirement-account-executive-order",
        "2026-05-03",
        "announcement",
    ),
    (
        "https://www.rev.com/transcripts/presidential-fitness-test-award",
        "2026-05-06",
        "ceremony",
    ),
    (
        "https://www.rev.com/transcripts/tariff-ruling-response",
        "2026-02-22",
        "announcement",
    ),
    (
        "https://www.rev.com/transcripts/epa-changes",
        "2026-02-15",
        "announcement",
    ),

    # --- Interviews (Trump speaking but with interviewer turns) ---
    (
        "https://www.rev.com/transcripts/60-minutes-trump-interview-on-whcd-shooting",
        "2026-04-27",
        "interview",
    ),
]

def load_corpus() -> list[Speech]:
    """Fetch (or load from cache) and parse the entire Trump speech corpus.
    
    Skips entries that fail to fetch.
    
    Returns:
        A list of Speech objects, one per successfully-loaded transcript.
    """
    corpus = []
    for url, date, event_type in TRUMP_SPEECHES:
        html = fetch_html(url)
        if html is None:
            print(f"  skipped (fetch failed): {url}")
            continue
        
        try:
            speech = build_speech(url, date, event_type, html)
        except Exception as e:
            # If parsing fails on one transcript, skip it but don't crash
            print(f"  skipped (parse failed): {url} — {type(e).__name__}: {e}")
            continue
        
        corpus.append(speech)
    
    return corpus