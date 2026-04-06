"""Rule-based and AI-assisted case evaluation for judgement mode."""

from __future__ import annotations

import re
from typing import Callable

HARM_KEYWORDS = {
    "steal", "stole", "theft", "hurt", "harm", "attack", "abuse", "cheat", "lied", "lie", "fraud", "blackmail",
}
SEVERE_HARM_KEYWORDS = {
    "kill", "murder", "assault", "terror", "kidnap", "arson", "poison", "extort", "weapon",
}
POSITIVE_KEYWORDS = {
    "help", "helped", "honest", "truth", "saved", "protect", "apologized", "apology", "donated", "volunteer",
}
JUSTIFICATION_KEYWORDS = {
    "because", "had to", "forced", "self defense", "self-defence", "necessity", "emergency", "to protect",
}
ILLEGAL_KEYWORDS = {
    "illegal", "crime", "criminal", "stole", "steal", "fraud", "forgery", "bribe", "bribery", "hack", "hacked",
    "drug", "drugs", "smuggle", "smuggled", "kidnap", "murder", "assault", "arson", "extort", "theft",
}
NECESSITY_MITIGATION_KEYWORDS = {
    "self defense", "self-defence", "to survive", "to save", "to protect", "medical emergency", "duress", "coerced",
    "threatened", "immediate danger",
}

POSITIVE_SENTIMENT_WORDS = {
    "good", "kind", "safe", "fair", "helpful", "honest", "mercy", "care", "ethical", "responsible", "compassion",
}
NEGATIVE_SENTIMENT_WORDS = {
    "bad", "harmful", "cruel", "violent", "dangerous", "selfish", "malicious", "unfair", "corrupt", "hostile",
}
INTENSIFIERS = {"very", "extremely", "seriously", "highly", "deeply", "totally"}


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z']+", text.lower())


def analyze_sentiment(case_text: str) -> dict[str, object]:
    """Simple lexicon sentiment pass used alongside rule keywords."""

    tokens = _tokenize(case_text)
    if not tokens:
        return {"polarity": 0, "label": "NEUTRAL", "positive_hits": [], "negative_hits": []}

    positive_hits: list[str] = []
    negative_hits: list[str] = []
    polarity = 0

    for idx, token in enumerate(tokens):
        boost = 2 if idx > 0 and tokens[idx - 1] in INTENSIFIERS else 1
        if token in POSITIVE_SENTIMENT_WORDS:
            positive_hits.append(token)
            polarity += boost
        elif token in NEGATIVE_SENTIMENT_WORDS:
            negative_hits.append(token)
            polarity -= boost

    label = "POSITIVE" if polarity > 1 else "NEGATIVE" if polarity < -1 else "NEUTRAL"
    return {
        "polarity": polarity,
        "label": label,
        "positive_hits": sorted(set(positive_hits)),
        "negative_hits": sorted(set(negative_hits)),
    }


def calculate_score(case_text: str) -> dict[str, object]:
    """Calculate score from keyword categories and sentiment signal."""

    lowered = (case_text or "").lower()
    tokens = _tokenize(case_text)
    sentiment = analyze_sentiment(case_text)

    harm_hits = [keyword for keyword in HARM_KEYWORDS if keyword in lowered]
    severe_hits = [keyword for keyword in SEVERE_HARM_KEYWORDS if keyword in lowered]
    positive_hits = [keyword for keyword in POSITIVE_KEYWORDS if keyword in lowered]
    justification_hits = [keyword for keyword in JUSTIFICATION_KEYWORDS if keyword in lowered]
    illegal_hits = [keyword for keyword in ILLEGAL_KEYWORDS if keyword in lowered]
    necessity_hits = [keyword for keyword in NECESSITY_MITIGATION_KEYWORDS if keyword in lowered]

    score = 0
    score += len(harm_hits) * -30
    score += len(severe_hits) * -50
    score += len(positive_hits) * 20
    score += len(justification_hits) * 10
    score += len(illegal_hits) * -35
    score += len(necessity_hits) * 20
    score += int(sentiment["polarity"]) * 6
    ethics_override_applied = False
    legality_flag = "LEGALITY UNCLEAR"

    if illegal_hits and not necessity_hits:
        score -= 20
        legality_flag = "ILLEGAL + UNNECESSARY"
    elif illegal_hits and necessity_hits:
        legality_flag = "ILLEGAL BUT CLAIMED NECESSARY"
    elif not illegal_hits and necessity_hits:
        legality_flag = "MITIGATED BY NECESSITY CONTEXT"

    unethical_signal = bool(harm_hits or severe_hits)
    very_short_input = len(tokens) <= 4
    if very_short_input and unethical_signal and -20 <= score <= 20:
        score -= 25
        ethics_override_applied = True

    if score > 20:
        verdict = "NOT GUILTY"
    elif score < -20:
        verdict = "GUILTY"
    else:
        verdict = "UNCLEAR"

    if score >= 15:
        severity = "LOW"
    elif score <= -50:
        severity = "HIGH"
    else:
        severity = "MEDIUM"

    return {
        "score": score,
        "verdict": verdict,
        "severity": severity,
        "harm_hits": harm_hits,
        "severe_hits": severe_hits,
        "positive_hits": positive_hits,
        "justification_hits": justification_hits,
        "sentiment": sentiment,
        "ethics_override_applied": ethics_override_applied,
        "illegal_hits": illegal_hits,
        "necessity_hits": necessity_hits,
        "legality_flag": legality_flag,
    }


def evaluate_case(case_id: int, case_text: str, ai_callable: Callable[[str], str]) -> dict[str, str | int]:
    """Evaluate a case using rule-based scoring plus an AI explanation."""

    scoring = calculate_score(case_text)
    structured_prompt = (
        "JUDGEMENT SYSTEM REQUEST\n"
        f"CASE ID: {case_id:03d}\n"
        f"CASE INPUT: {case_text}\n"
        f"RULE SCORE: {scoring['score']}\n"
        f"RULE VERDICT: {scoring['verdict']}\n"
        f"RULE SEVERITY: {scoring['severity']}\n\n"
        f"SENTIMENT: {scoring['sentiment']['label']} ({scoring['sentiment']['polarity']})\n"
        f"LEGALITY ASSESSMENT: {scoring['legality_flag']}\n"
        f"ETHICS OVERRIDE APPLIED: {scoring['ethics_override_applied']}\n"
        f"KEYWORDS DETECTED: harm={scoring['harm_hits']}, severe={scoring['severe_hits']}, "
        f"positive={scoring['positive_hits']}, justification={scoring['justification_hits']}, "
        f"illegal={scoring['illegal_hits']}, necessity={scoring['necessity_hits']}\n\n"
        "Respond in exactly three concise sections with clear labels:\n"
        "INTENT ANALYSIS: ...\n"
        "CONSEQUENCE ANALYSIS: ...\n"
        "FINAL REASONING: ...\n"
        "Keep courtroom tone and avoid extra headings."
    )

    ai_response = ai_callable(structured_prompt).strip()

    intent = "Analysis unavailable."
    consequence = "Analysis unavailable."
    final_reasoning = ai_response if ai_response else "No additional AI reasoning returned."

    for line in ai_response.splitlines():
        text = line.strip()
        upper = text.upper()
        if upper.startswith("INTENT ANALYSIS:"):
            intent = text.split(":", 1)[1].strip() or intent
        elif upper.startswith("CONSEQUENCE ANALYSIS:"):
            consequence = text.split(":", 1)[1].strip() or consequence
        elif upper.startswith("FINAL REASONING:"):
            final_reasoning = text.split(":", 1)[1].strip() or final_reasoning

    return {
        "case_id": case_id,
        "input": case_text,
        "score": int(scoring["score"]),
        "verdict": str(scoring["verdict"]),
        "severity": str(scoring["severity"]),
        "sentiment_label": str(scoring["sentiment"]["label"]),
        "sentiment_polarity": int(scoring["sentiment"]["polarity"]),
        "legality_flag": str(scoring["legality_flag"]),
        "ethics_override_applied": bool(scoring["ethics_override_applied"]),
        "intent_analysis": intent,
        "consequence_analysis": consequence,
        "final_reasoning": final_reasoning,
    }


def format_verdict_output(result: dict[str, str | int]) -> str:
    """Render structured case output for the courtroom panel."""

    return (
        f"CASE FILE //--// {int(result['case_id']):03d}\n"
        f"VERDICT: {result['verdict']}\n"
        f"SEVERITY: {result['severity']}\n"
        f"SCORE: {result['score']}\n\n"
        f"SENTIMENT: {result['sentiment_label']} ({result['sentiment_polarity']})\n\n"
        f"LEGALITY ASSESSMENT: {result['legality_flag']}\n\n"
        f"ETHICS OVERRIDE APPLIED: {result['ethics_override_applied']}\n\n"
        "INTENT ANALYSIS:\n"
        f"{result['intent_analysis']}\n\n"
        "CONSEQUENCE ANALYSIS:\n"
        f"{result['consequence_analysis']}\n\n"
        "FINAL REASONING:\n"
        f"{result['final_reasoning']}"
    )
