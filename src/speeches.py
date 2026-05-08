"""
Parsing and storage of speech transcripts.

This module owns:
- The Speech and SpeechTurn data model
- Parsing transcripts from various sources (Rev, Roll Call, etc.)
- Speaker name normalization
- Filtering turns by speaker
"""
import re
from dataclasses import dataclass
from src.fetcher import html_to_text

# Speakers to normalize to a canonical form.
# Anyone not in this dict keeps their original name.
SPEAKER_NORMALIZATIONS: dict[str, str] = {
    "President Donald J. Trump": "Trump",
    "Donald Trump": "Trump",
    "Donald J. Trump": "Trump",
    "President Trump": "Trump",
    "President Donald Trump": "Trump",
    "US President Donald Trump": "Trump"
}

@dataclass(frozen=True)
class SpeechTurn:
    """A single uninterrupted speaking turn by one speaker."""
    speaker: str             # normalized speaker name (e.g. "Trump", "Oz")
    text: str                # the spoken words, cleaned
    timestamp_seconds: int   # seconds from start of speech


@dataclass(frozen=True)
class Speech:
    """A single speech or event with one or more speakers."""
    source_url: str
    title: str
    date: str                # ISO date string YYYY-MM-DD
    event_type: str          # "rally", "press_conference", "interview", etc.
    turns: tuple[SpeechTurn, ...]   # frozen sequence — note: tuple, not list

    def turns_by(self, speaker: str) -> list[SpeechTurn]:
        """Return only turns by the given speaker (matched case-insensitively)."""
        return [t for t in self.turns if t.speaker.lower() == speaker.lower()]

    def text_by(self, speaker: str) -> str:
        """Return all text spoken by the given speaker, joined."""
        return " ".join(t.text for t in self.turns_by(speaker))
    

def normalize_speaker(raw_name: str) -> str:
    """Convert a raw speaker label into a canonical name.
    
    Strips trailing whitespace AND trailing punctuation (colons, periods)
    that sometimes get captured by the speaker regex when source HTML has
    the speaker name and timestamp running together unusually.
    """
    cleaned = raw_name.strip().rstrip(":.").strip()
    return SPEAKER_NORMALIZATIONS.get(cleaned, cleaned)


def _timestamp_to_seconds(ts: str) -> int:
    """Convert "MM:SS" or "HH:MM:SS" to total seconds.
    
    Examples:
        "00:13"    -> 13
        "12:34"    -> 754  (12*60 + 34)
        "1:02:30"  -> 3750 (1*3600 + 2*60 + 30)
    """
    times = ts.split(":")
    times.reverse()
    seconds = 0
    for i,unit in enumerate(times):
        seconds += int(unit) * 60**i
    return seconds


def parse_transcript(text: str) -> list[SpeechTurn]:
    """Parse a Rev transcript into speech turns.
    
    Handles two kinds of paragraph headers:
        Speaker Name (MM:SS):   ← introduces a new speaker turn
        (MM:SS)                  ← continuation of the previous speaker
    
    Continuations are merged into the most recent speaker's turn.
    """
    # The (.+?)\s+ group is optional — present for full headers, absent for orphans.
    # The trailing :? is optional — present for full headers, absent for orphans.
    marker_pattern = re.compile(r"^(?:([^\n]{1,50}?)\s+)?\(\s*(\d+:\d+(?::\d+)?)\s*\):?",re.MULTILINE)
    
    turns: list[SpeechTurn] = []
    current_speaker: str | None = None
    
    matches = list(marker_pattern.finditer(text))
    for i, match in enumerate(matches):
        speaker_raw = match.group(1)  # None for orphan timestamps
        timestamp_str = match.group(2)
        
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        
        if not body:
            continue
        
        if speaker_raw is not None:
            current_speaker = normalize_speaker(speaker_raw.strip())
            turns.append(SpeechTurn(
                speaker=current_speaker,
                text=body,
                timestamp_seconds=_timestamp_to_seconds(timestamp_str),
            ))
        else:
            if current_speaker is None:
                continue
            prev = turns[-1]
            turns[-1] = SpeechTurn(
                speaker=prev.speaker,
                text=prev.text + " " + body,
                timestamp_seconds=prev.timestamp_seconds,
            )
    
    return turns


def build_speech(url, date, event_type, html) -> Speech:
    """Construct a Speech from raw HTML and corpus metadata."""
    text = html_to_text(html)
    turns = parse_transcript(text)
    title = url.rstrip("/").rsplit("/", 1)[-1].replace("-", " ").title()
    return Speech(
        source_url=url,
        title=title,
        date=date,
        event_type=event_type,
        turns=tuple(turns),
    )