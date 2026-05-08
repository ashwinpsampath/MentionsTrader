from pathlib import Path
from src.speeches import parse_transcript

text = Path("tests/fixtures/trumprx.txt").read_text()
turns = parse_transcript(text)

print(f"Found {len(turns)} turns")
print()

for t in turns[:5]:
    print(f"[{t.timestamp_seconds}s] {t.speaker}:")
    print(f"  {t.text[:100]}...")
    print()

# Show speaker distribution
from collections import Counter
speakers = Counter(t.speaker for t in turns)
print("Speaker turn counts:")
for speaker, count in speakers.most_common():
    print(f"  {speaker}: {count}")

# ... existing code ...

# Quick sanity check on speaker filtering
from src.speeches import Speech

speech = Speech(
    source_url="https://www.rev.com/transcripts/trumprx-announcement",
    title="TrumpRX Announcement",
    date="2025-09-30",  # approximate; we'll fetch the real date later
    event_type="announcement",
    turns=tuple(turns),
)

trump_text = speech.text_by("Trump")
oz_text = speech.text_by("Dr. Mehmet Oz")

print(f"\nTrump total characters: {len(trump_text)}")
print(f"Oz total characters: {len(oz_text)}")
print(f"\nDoes Trump's text contain 'most favored nation'? {'most favored nation' in trump_text.lower()}")
print(f"Does Trump's text contain 'IVF'? {'IVF' in trump_text}")
print(f"Does Oz's text contain 'IVF'? {'IVF' in oz_text}")