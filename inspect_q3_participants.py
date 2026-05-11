# inspect_q3_participants.py
from src.fetcher import fetch_html, html_to_markdown

URL = "https://www.fool.com/earnings/call-transcripts/2025/11/03/hims-hers-hims-q3-2025-earnings-call-transcript/"

html = fetch_html(URL)
md = html_to_markdown(html)

# Show first 4000 chars after stripping all the navigation
# (everything before the first Date/Time line is chrome)
import re

# Find where the actual content begins
date_match = re.search(r"(Monday|Tuesday|Wednesday|Thursday|Friday).{0,30}20\d\d", md)
start = date_match.start() if date_match else 0

print(md[start:start + 4000])