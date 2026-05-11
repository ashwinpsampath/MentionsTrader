# inspect_failures.py
from src.fetcher import fetch_html, html_to_markdown
from src.speeches import parse_motley_fool_participants, parse_motley_fool_transcript

URLS = [
    ("Q1 2026 ", "https://www.fool.com/earnings/call-transcripts/2026/02/23/hims-hers-hims-earnings-call-transcript/"),
    ("Q3 2025 ", "https://www.fool.com/earnings/call-transcripts/2025/11/03/hims-hers-hims-q3-2025-earnings-call-transcript/"),
]

for label, url in URLS[1:]:
    print(f"\n=== {label} ===")
    html = fetch_html(url)
    md = html_to_markdown(html)
    
    participants = parse_motley_fool_participants(md)
    turns = parse_motley_fool_transcript(md)
    print(f"Participants: {participants}")
    print(f"Turn count: {len(turns)}")
    
    # Show what section headers exist in the markdown
    import re
    headers = re.findall(r"^(.{1,80})\n[-=]{3,}\s*$", md, re.MULTILINE)
    print(f"Section headers found: {headers[:15]}")
    
    # Show the first speaker label format we can find
    speaker_samples = re.findall(r"^\*\*[^*\n]{1,80}\*\*", md, re.MULTILINE)[:5]
    print(f"First speaker patterns: {speaker_samples}")

    # Show first 3 actual turns we parsed
    turns = parse_motley_fool_transcript(md)
    print(f"\nFirst 3 turns:")
    for t in turns[:3]:
        print(f"  Speaker: '{t.speaker}'")
        print(f"  Text: {t.text[:150]}")
        print()

    # And — crucially — search the full markdown for **Name:** patterns to confirm they exist
    real_speakers = re.findall(r"^\*\*([^*\n]{1,80}):\*\*", md, re.MULTILINE)[:10]
    print(f"Colon-ending bold patterns found in full doc: {real_speakers}")

    operator_count = sum(1 for t in turns if t.speaker == "Operator")
    print(f"Operator turns: {operator_count}")
    print(f"Operator first appears at turn index: {next((i for i, t in enumerate(turns) if t.speaker == 'Operator'), 'NEVER')}")