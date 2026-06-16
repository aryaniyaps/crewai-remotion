from __future__ import annotations

import re

AMBIGUOUS_PATTERNS = [
    r"^\s*\w{1,3}\s*$",
    r"\b(something|stuff|things)\b",
    r"\b\d+\s+(tools|tips|apps|ways|hacks|ideas)\b",
    r"^(ai|marketing|productivity|startup)\s*$",
]
CLEAR_PATTERNS = [
    r"\bvs\.?\b",
    r"[A-Z][a-z]+,\s+[A-Z]",
]


def ambiguity_score(topic: str) -> float:
    t = topic.strip()
    if len(t.split()) < 4:
        return 0.85
    score = 0.2
    for pat in AMBIGUOUS_PATTERNS:
        if re.search(pat, t, re.I):
            score += 0.35
    for pat in CLEAR_PATTERNS:
        if re.search(pat, t):
            score -= 0.3
    if re.search(r"\b\d+\s+\w+", t) and not re.search(r"\b(Notion|Linear|Stripe|OpenAI)\b", t, re.I):
        if re.search(r"\b(tools|tips|apps)\b", t, re.I):
            score += 0.25
    return max(0.0, min(1.0, score))


def is_ambiguous(topic: str, threshold: float = 0.5) -> bool:
    return ambiguity_score(topic) >= threshold
