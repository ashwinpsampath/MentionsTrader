"""
LLM-based probability adjustment for mention market predictions.

This module owns:
- Asking an LLM whether a phrase is more/less likely than usual to be said
- Returning a calibrated MULTIPLIER on the base rate, not an absolute probability
- Structured output via Anthropic tool use (no parsing of free-form text)

Design principle: the LLM produces a *delta from baseline*, not a raw probability.
LLMs are known to be poorly calibrated when asked "what's the probability of X?"
but reasonably good at "is X more or less likely than usual?" So we anchor on
the base rate and let the LLM nudge it.

Final probability formula (used elsewhere):
    P_final = base_rate * adjustment.multiplier

Where multiplier is in [0.5, 1.5] — capped to prevent extreme LLM outputs from
overwhelming the base rate signal.
"""
import os
from dataclasses import dataclass
from typing import Literal

import anthropic


# ============================================================
# Data model
# ============================================================

Confidence = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class ProbabilityAdjustment:
    """The LLM's view on whether to nudge the base rate up or down.

    Attributes:
        phrase: The target phrase being evaluated.
        multiplier: How much to scale the base rate. 1.0 = no change.
                    Capped to [0.5, 1.5] by the calling code.
        confidence: How confident the LLM is in its adjustment.
        reasoning: Short explanation, for auditing and debugging.
        top_factors: Specific evidence points the LLM considered.
    """
    phrase: str
    multiplier: float
    confidence: Confidence
    reasoning: str
    top_factors: tuple[str, ...]

    def apply_to(self, base_rate: float) -> float:
        """Apply this adjustment to a base rate, clamping to [0, 1]."""
        # Clamp multiplier to [0.5, 1.5] to prevent runaway adjustments
        clamped = max(0.5, min(1.5, self.multiplier))
        result = base_rate * clamped
        return max(0.0, min(1.0, result))


# ============================================================
# The tool schema for structured output
# ============================================================
# Using Anthropic's tool use means we get back a typed JSON object,
# not free-form text we have to parse. The model is forced to fill in
# every required field, so we never get half-formed responses.

_ADJUSTMENT_TOOL = {
    "name": "submit_probability_adjustment",
    "description": (
        "Submit your assessment of how the recent context should adjust the "
        "base rate for this phrase. You MUST call this tool exactly once."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "multiplier": {
                "type": "number",
                "description": (
                    "How much to scale the base rate. Use 1.0 if context is "
                    "neutral (no reason to think the phrase is more or less "
                    "likely than usual). Use values >1.0 if recent context "
                    "makes the phrase MORE likely. Use values <1.0 if LESS "
                    "likely. Stay within 0.5 to 1.5 — extreme adjustments "
                    "should be rare and well-justified."
                ),
                "minimum": 0.5,
                "maximum": 1.5,
            },
            "confidence": {
                "type": "string",
                "enum": ["low", "medium", "high"],
                "description": (
                    "How confident are you in this adjustment? Use 'low' "
                    "when context is sparse or ambiguous. Use 'high' only "
                    "when there's specific recent evidence directly bearing "
                    "on whether this phrase will come up."
                ),
            },
            "reasoning": {
                "type": "string",
                "description": (
                    "One or two sentences explaining your adjustment. Be "
                    "concrete: reference specific events, news, or company "
                    "circumstances. Avoid vague language."
                ),
            },
            "top_factors": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "1 to 3 short, specific evidence points you considered. "
                    "E.g. 'Recent tariff escalation in news', 'Company "
                    "guidance update last week mentioned topic'."
                ),
                "minItems": 1,
                "maxItems": 3,
            },
        },
        "required": ["multiplier", "confidence", "reasoning", "top_factors"],
    },
}


# ============================================================
# The prompt
# ============================================================

_SYSTEM_PROMPT = """You are a calibrated quantitative analyst evaluating a \
prediction market. Your job is NOT to predict absolute probabilities — that's \
handled separately by a historical base-rate model.

Your job is to assess whether RECENT CONTEXT (news, company circumstances, \
current events) makes a target phrase MORE or LESS likely than usual to be \
mentioned in an upcoming corporate earnings call.

You return a multiplier on the base rate:
- 1.0 = no adjustment, context is neutral
- 1.2 = phrase is somewhat more likely than usual
- 0.7 = phrase is somewhat less likely than usual

IMPORTANT GUARDRAILS:
- Stay between 0.5 and 1.5. Extreme adjustments are rarely justified.
- Default to 1.0 (no adjustment) when context is sparse, vague, or \
not specifically about this phrase.
- Set confidence='low' when you're guessing.
- Be specific in your reasoning. Vague rationales like "general market \
conditions" should produce 1.0 with low confidence.

You MUST call the submit_probability_adjustment tool exactly once."""


def _build_user_prompt(
    phrase: str,
    company: str,
    base_rate: float,
    context: str,
) -> str:
    """Build the user message describing the specific prediction question."""
    return f"""COMPANY: {company}
TARGET PHRASE: "{phrase}"
HISTORICAL BASE RATE: {base_rate:.1%} (fraction of past earnings calls where \
this phrase appeared)

RECENT CONTEXT (news, filings, market conditions from the last 30 days):
{context if context.strip() else "[No specific context provided.]"}

Question: Should we adjust the historical base rate up or down based on \
this recent context? Submit your adjustment via the tool."""


# ============================================================
# The main entry point
# ============================================================

def get_adjustment(
    phrase: str,
    company: str,
    base_rate: float,
    context: str,
    *,
    model: str = "claude-sonnet-4-6",
    client: anthropic.Anthropic,
) -> ProbabilityAdjustment:
    """Ask the LLM to adjust a base rate given recent context.

    Args:
        phrase: The target phrase (e.g. "tariff", "weight loss").
        company: Company name or ticker (e.g. "HIMS").
        base_rate: Historical rate from corpus, in [0, 1].
        context: Free text describing recent news, filings, etc.
        model: Anthropic model to use.
        client: Optional pre-built Anthropic client (useful for testing).

    Returns:
        A ProbabilityAdjustment object.

    Raises:
        ValueError: if the LLM doesn't call the tool (shouldn't happen
            given the system prompt, but possible).
    """

    user_prompt = _build_user_prompt(phrase, company, base_rate, context)

    response = client.messages.create(
        model=model,
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        tools=[_ADJUSTMENT_TOOL],
        tool_choice={"type": "tool", "name": "submit_probability_adjustment"},
        messages=[{"role": "user", "content": user_prompt}],
    )

    # Extract the tool use block
    for block in response.content:
        if block.type == "tool_use" and block.name == "submit_probability_adjustment":
            data = block.input
            return ProbabilityAdjustment(
                phrase=phrase,
                multiplier=float(data["multiplier"]),
                confidence=data["confidence"],
                reasoning=data["reasoning"],
                top_factors=tuple(data["top_factors"]),
            )

    raise ValueError(
        f"LLM did not call the expected tool. Response: {response.content}"
    )