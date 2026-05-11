"""
Compute base rates: how often does Trump say a given phrase in the corpus?

A "base rate" is the fraction of past speeches in which a target phrase
appeared. This is the foundation of our probability engine — for any new
mention market, we start with: "given history, how often does this happen?"
"""
import re
from dataclasses import dataclass

from src.speeches import Speech


@dataclass(frozen=True)
class BaseRate:
    """The historical occurrence rate of a phrase in a corpus.
    
    Attributes:
        phrase: The phrase we searched for.
        matched_speeches: Count of speeches that contained the phrase.
        total_speeches: Total speeches in the corpus.
        rate: matched / total — the naive maximum-likelihood estimate.
        smoothed_rate: (matched + α) / (total + 2α) — Laplace-smoothed estimate,
                       with α=1 by default. More appropriate for prediction when
                       the sample is small or when the naive rate is 0 or 1.
        matched_titles: Titles of speeches where the phrase appeared.
    """
    phrase: str
    matched_speeches: int
    total_speeches: int
    rate: float
    smoothed_rate: float
    matched_titles: tuple[str, ...]


def _phrase_appears(phrase: str, text: str) -> bool:
    """Does the phrase appear as a whole word/phrase in the text?
    
    Matches the phrase itself plus simple plural/possessive variants
    (trailing s, 's, or es). Case-insensitive.
    """
    pattern = r"\b" + re.escape(phrase) + r"(?:'s|s|es)?\b"
    return re.search(pattern, text, re.IGNORECASE) is not None


def compute_base_rate(
    phrase: str,
    corpus: list[Speech],
    smoothing_alpha: float = 1.0,
) -> BaseRate:
    """Compute the base rate for a phrase in the given corpus.
    
    Args:
        phrase: Target phrase. Case-insensitive. Plural/possessive variants ok.
        corpus: List of Speech objects to search.
        smoothing_alpha: Laplace smoothing strength. 1.0 is standard.
                         Larger values pull more toward 50% (more skeptical
                         of small-sample evidence).
    
    Returns:
        A BaseRate object with full details about the match.
    """
    total = len(corpus)
    matched_titles = []
    for speech in corpus:
        text = speech.text_by_company();
        if _phrase_appears(phrase, text):
            matched_titles.append(speech.title)
    
    matched = len(matched_titles)
    smoothed_rate = (matched + smoothing_alpha) / (total + 2 * smoothing_alpha)

    return BaseRate(phrase=phrase,
                    matched_speeches=matched,
                    total_speeches=total,
                    rate=matched / total,
                    smoothed_rate=smoothed_rate,
                    matched_titles=tuple(matched_titles))
    