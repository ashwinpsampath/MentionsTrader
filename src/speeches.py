"""
Parsing and storage of earnings call transcripts.

This module owns:
- The Speech and SpeechTurn data model
- Parsing transcripts from Motley Fool
- Identifying company representatives vs analysts within a transcript

Input format note:
    Parsers expect MARKDOWN-formatted text, not raw HTML. Use
    fetcher.html_to_markdown() to convert before parsing. Markdown
    preserves the speaker bolding (**Name:**) and section headers (##)
    that we anchor on.
"""
import re
from dataclasses import dataclass
from src.fetcher import html_to_markdown


# ============================================================
# Data model
# ============================================================

@dataclass(frozen=True)
class SpeechTurn:
    """A single uninterrupted speaking turn by one speaker."""
    speaker: str   # name as it appears in the source (e.g. "Ashwin Sampath")
    text: str      # the spoken words


@dataclass(frozen=True)
class Speech:
    """A single earnings call.

    company_representatives lists the names that count as "the company speaking"
    — everyone else (analysts) is excluded from company-side text queries.
    """
    source_url: str
    title: str
    date: str                # ISO date string YYYY-MM-DD
    ticker: str              # e.g. "MCD"
    turns: tuple[SpeechTurn, ...]
    company_representatives: tuple[str, ...]

    def text_by_company(self) -> str:
        """All text spoken by company representatives plus the Operator.

        For a Kalshi mention market that resolves on "any company representative
        (including the operator) saying X", this is the text we should be searching.
        """
        allowed = set(self.company_representatives) | {"Operator"}
        return " ".join(t.text for t in self.turns if t.speaker in allowed)


# ============================================================
# Participants list parser
# ============================================================
# Looking for a section like:
#
#   ## CALL PARTICIPANTS
#
#   - President and Chief Executive Officer — Christopher Kempczinski
#   - Executive Vice President and Chief Financial Officer — Ian Borden
#   - Vice President, Investor Relations — Dexter Congbalay
#
#   ## TAKEAWAYS  ← stops here


_PARTICIPANTS_HEADER = re.compile(
    r"^##\s+CALL PARTICIPANTS\s*$",
    re.MULTILINE | re.IGNORECASE,   # ← add the flag
)

_NEXT_SECTION_HEADER = re.compile(r"^##\s+\S", re.MULTILINE)

# Matches a list item: "- Title — Name"
_PARTICIPANT_LINE = re.compile(r"^-?\s*.+?\s+\u2014\s+(.+?)\s*$", re.MULTILINE)


def parse_motley_fool_participants(text: str) -> list[str]:
    """Extract company representative names from the CALL PARTICIPANTS section.

    Args:
        text: Markdown-formatted page content.

    Returns:
        List of participant names in the order they appear.
        Empty list if the section can't be found.
    """
    header_match = _PARTICIPANTS_HEADER.search(text)
    if not header_match:
        return []

    # Slice from end of participants header to the next ## section header.
    section_start = header_match.end()
    next_header_match = _NEXT_SECTION_HEADER.search(text, pos=section_start)
    section_end = next_header_match.start() if next_header_match else len(text)

    section = text[section_start:section_end]
    return [m.group(1).strip() for m in _PARTICIPANT_LINE.finditer(section)]


# ============================================================
# Transcript turns parser
# ============================================================
# Looking for:
#
#   ## Full Conference Call Transcript
#
#   **Christopher Kempczinski:** Good morning, everyone...
#
#   **Ian Borden:** Thanks, Chris...
#
#   **Operator:** *[Operator Instructions]*
#
#   ... continues until the next ## section ...


_TRANSCRIPT_START = re.compile(
    r"^##\s+Full Conference Call Transcript\s*$",
    re.MULTILINE | re.IGNORECASE,   # ← add the flag
)

# A speaker turn starts with **Name:** at the beginning of a line.
# The 80-char cap on the name is defense-in-depth against formatting glitches
# greedily matching across multiple turns.
_SPEAKER_LINE = re.compile(
    r"^\*\*([^\n*]{1,80}?):\*\*\s*",
    re.MULTILINE,
)


def parse_motley_fool_transcript(text: str) -> list[SpeechTurn]:
    """Parse a Motley Fool earnings call transcript into speech turns.

    Args:
        text: Markdown-formatted page content.

    Returns:
        List of SpeechTurn objects in document order. Speaker names are kept
        as-is from the source — no normalization needed since earnings call
        speakers use their real names consistently.
    """
    start_match = _TRANSCRIPT_START.search(text)
    if not start_match:
        return []

    transcript_start = start_match.end()
    next_section = _NEXT_SECTION_HEADER.search(text, pos=transcript_start)
    transcript_end = next_section.start() if next_section else len(text)

    transcript = text[transcript_start:transcript_end]

    speaker_matches = list(_SPEAKER_LINE.finditer(transcript))

    turns: list[SpeechTurn] = []
    for i, match in enumerate(speaker_matches):
        speaker = match.group(1).strip()

        body_start = match.end()
        body_end = (
            speaker_matches[i + 1].start()
            if i + 1 < len(speaker_matches)
            else len(transcript)
        )
        body = transcript[body_start:body_end].strip()

        if not body:
            continue

        turns.append(SpeechTurn(speaker=speaker, text=body))

    return turns

def build_speech_from_motley_fool(url, date, ticker, html) -> Speech:
    md = html_to_markdown(html)
    participants = parse_motley_fool_participants(md)
    turns = parse_motley_fool_transcript(md)
    return Speech(
        source_url=url,
        title=...,  # derive from URL or fetch page title
        date=date,
        ticker=ticker,
        turns=tuple(turns),
        company_representatives=tuple(participants),
    )