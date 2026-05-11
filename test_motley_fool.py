"""Test parsing one McDonald's earnings call."""
from src.fetcher import fetch_html, html_to_markdown
from src.speeches import parse_motley_fool_participants, parse_motley_fool_transcript


URL = "https://www.fool.com/earnings/call-transcripts/2026/05/07/mcdonalds-mcd-q1-2026-earnings-transcript/"

html = fetch_html(URL, force_refresh=True)
md = html_to_markdown(html)

participants = parse_motley_fool_participants(md)
print(f"Participants ({len(participants)}):")
for p in participants:
    print(f"  - {p}")

turns = parse_motley_fool_transcript(md)
print(f"\nTotal turns: {len(turns)}")

# Speaker distribution
from collections import Counter
labels = Counter(t.speaker for t in turns)
print("\nSpeaker turn counts:")
for label, count in labels.most_common():
    in_company = "✓" if label in participants else " "
    print(f"  [{in_company}] {label}: {count}")

# Total characters of company-side text
company_set = set(participants) | {"Operator"}
company_chars = sum(len(t.text) for t in turns if t.speaker in company_set)
print(f"\nCompany-side text: {company_chars:,} chars")