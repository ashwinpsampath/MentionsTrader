"""Test the LLM context layer with hand-crafted scenarios.

These scenarios let us see if the LLM is producing sensible adjustments
WITHOUT needing real news context. Once these look reasonable, we move
on to wiring up real news fetching.

Run with: uv run python test_llm_context.py
"""
from src.llm_context import get_adjustment
from anthropic import Anthropic
import dotenv
import os
import time

dotenv.load_dotenv()


# Each test case: a scenario where we have a strong prior about what
# the LLM SHOULD do. If the model's adjustment goes the opposite direction,
# that tells us the prompt needs work or the model is poorly calibrated.

TEST_CASES = [
    {
        "name": "Strong positive signal — direct recent news",
        "phrase": "tariff",
        "company": "HIMS",
        "base_rate": 0.50,
        "context": (
            "Last week, the Biden administration announced new tariffs on "
            "pharmaceutical imports from India, where HIMS sources much of "
            "its generic GLP-1 ingredients. Industry analysts have been "
            "publishing pieces all week about how this affects telehealth "
            "companies. HIMS's CEO Andrew Dudum has not commented publicly yet."
        ),
        "expected_direction": "up",
    },
    {
        "name": "Strong negative signal — topic resolved/moved on",
        "phrase": "compounding",
        "company": "HIMS",
        "base_rate": 0.75,
        "context": (
            "Three months ago, HIMS pivoted away from compounded GLP-1s "
            "after FDA enforcement changes. The compounding controversy "
            "dominated their last two calls, but management announced in "
            "October they've fully transitioned to FDA-approved formulations "
            "and no longer plan to discuss the compounding chapter. They've "
            "shifted messaging entirely to longevity and lab testing services."
        ),
        "expected_direction": "down",
    },
    {
        "name": "Neutral / sparse context — should default near 1.0",
        "phrase": "innovation",
        "company": "HIMS",
        "base_rate": 0.60,
        "context": (
            "Stock is up 3% this month. Q3 earnings were generally well-received."
        ),
        "expected_direction": "neutral",
    },
    {
        "name": "Vague positive — should be cautious",
        "phrase": "guidance",
        "company": "HIMS",
        "base_rate": 0.80,
        "context": (
            "Some analysts expect HIMS to discuss outlook. Market conditions "
            "are generally favorable for telehealth."
        ),
        "expected_direction": "slight up or neutral",
    },
    {
        "name": "Specific upcoming event",
        "phrase": "longevity",
        "company": "HIMS",
        "base_rate": 0.30,
        "context": (
            "HIMS announced last week that their longevity specialty product "
            "line — including peptides, coenzymes, and GIP treatments — will "
            "launch in early 2026, which is the topic of the upcoming call. "
            "Press releases have heavily emphasized longevity as the new "
            "strategic priority."
        ),
        "expected_direction": "strongly up",
    },
]


def main() -> None:
    print("Testing LLM context layer with hand-crafted scenarios.\n")
    print("Each scenario has an EXPECTED direction. If the LLM's adjustment")
    print("goes the opposite way, the prompt or model needs work.\n")
    print("=" * 80)

    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    for i, case in enumerate(TEST_CASES, 1):
        print(f"\n[{i}/{len(TEST_CASES)}] {case['name']}")
        print(f"  Phrase: '{case['phrase']}'")
        print(f"  Base rate: {case['base_rate']:.0%}")
        print(f"  Expected direction: {case['expected_direction']}")
        print(f"  Context (first 100 chars): {case['context'][:100]}...")

        try:
            adj = get_adjustment(
                phrase=case["phrase"],
                company=case["company"],
                base_rate=case["base_rate"],
                context=case["context"],
                client=client
            )
        except Exception as e:
            print(f"  ERROR: {type(e).__name__}: {e}")
            continue

        adjusted_rate = adj.apply_to(case["base_rate"])

        print(f"\n  → Multiplier:    {adj.multiplier:.2f}")
        print(f"  → Confidence:    {adj.confidence}")
        print(f"  → Adjusted rate: {case['base_rate']:.0%} → {adjusted_rate:.0%}")
        print(f"  → Reasoning:     {adj.reasoning}")
        print(f"  → Top factors:")
        for f in adj.top_factors:
            print(f"      - {f}")
        print("-" * 80)


if __name__ == "__main__":
    start = time.time()
    main()
    end = time.time()
    print(end - start)