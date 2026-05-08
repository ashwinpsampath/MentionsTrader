"""See exactly what html_to_text produces for one transcript."""
from src.fetcher import fetch_html, html_to_text

URL = "https://www.rev.com/transcripts/trumprx-announcement"

html = fetch_html(URL)
text = html_to_text(html)

print(f"=== Cleaned text length: {len(text):,} chars ===\n")
print("=== First 3000 characters ===")
print(text[:3000])
print("\n=== Looking for speaker patterns ===")
import re
speaker_matches = re.findall(r"^.{1,80}\(\d+:\d+(?::\d+)?\):", text, re.MULTILINE)
print(f"Found {len(speaker_matches)} speaker-like lines")
for m in speaker_matches[:10]:
    print(f"  '{m}'")

"""Look at speaker labels in a specific transcript."""
from collections import Counter
from src.fetcher import fetch_html, html_to_text
from src.speeches import parse_transcript

URL = "https://www.rev.com/transcripts/trump-speaks-at-tpusa-event"

html = fetch_html(URL)
text = html_to_text(html)
turns = parse_transcript(text)

print(f"Total turns: {len(turns)}")
print(f"\nSpeaker label counts:")
labels = Counter(t.speaker for t in turns)
for label, count in labels.most_common():
    print(f"  '{label}': {count}")

print(f"\nFirst 3 turns:")
for t in turns[:3]:
    print(f"  [{t.timestamp_seconds}s] {t.speaker}:")
    print(f"    {t.text[:200]}")