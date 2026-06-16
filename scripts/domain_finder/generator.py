"""Generate pronounceable, brand-style .com SLD candidates."""

from __future__ import annotations

import itertools
import random

from .analyzers import alternates_vowels_consonants, has_double_letters

CONSONANTS = "bcdfghjklmnprstv"
CONSONANTS_START = "bcdfghjklmnprstvw"
VOWELS = "aeiou"

# Prefix/suffix combos chosen to avoid internal double letters when merged.
TECH_ENDINGS = ("ex", "on", "um", "ar", "en", "ra", "va", "no", "zo", "el", "or")
TECH_PREFIXES = ("neo", "ver", "syn", "lum", "nex", "zen", "ora", "vel", "arc", "sol", "nova", "vera")


def _pick(pool: str, rng: random.Random, *, avoid: str | None = None) -> str:
    choices = [ch for ch in pool if ch != avoid]
    return rng.choice(choices)


def _from_pattern(pattern: str, rng: random.Random) -> str:
    out: list[str] = []
    for token in pattern:
        prev = out[-1] if out else None
        if token == "C":
            out.append(_pick(CONSONANTS, rng, avoid=prev))
        elif token == "V":
            out.append(_pick(VOWELS, rng, avoid=prev))
        elif token == "S":
            out.append(_pick(CONSONANTS_START, rng, avoid=prev))
        else:
            raise ValueError(f"Unknown pattern token: {token}")
    return "".join(out)


def _is_public_friendly(sld: str) -> bool:
    if has_double_letters(sld):
        return False
    if not alternates_vowels_consonants(sld):
        return False
    return True


def generate_candidates(
    *,
    count: int = 500,
    min_len: int = 4,
    max_len: int = 6,
    seed: int | None = None,
) -> list[str]:
    rng = random.Random(seed)
    seen: set[str] = set()
    candidates: list[str] = []

    # Strict alternation patterns — easiest for the public to pronounce.
    patterns = [
        "CVCV",
        "CVCVC",
        "VCVC",
        "VCVCV",
        "SVCV",
        "SVCVC",
        "CVSCV",
    ]

    attempts = 0
    while len(candidates) < count and attempts < count * 20:
        attempts += 1
        if rng.random() < 0.25:
            prefix = rng.choice(TECH_PREFIXES)
            suffix = rng.choice(TECH_ENDINGS)
            sld = (prefix + suffix)[:max_len]
        else:
            pattern = rng.choice(patterns)
            sld = _from_pattern(pattern, rng)

        sld = sld.lower()
        if len(sld) < min_len or len(sld) > max_len:
            continue
        if sld in seen or not sld.isalpha():
            continue
        if not _is_public_friendly(sld):
            continue
        seen.add(sld)
        candidates.append(sld)

    # Exhaustive CVCV sweep (never contains double letters).
    for c1, v1, c2, v2 in itertools.product(CONSONANTS_START, VOWELS, CONSONANTS, VOWELS):
        sld = f"{c1}{v1}{c2}{v2}"
        if sld not in seen:
            seen.add(sld)
            candidates.append(sld)

    for c1, v1, c2, v2, c3 in itertools.product(
        CONSONANTS_START, VOWELS, CONSONANTS, VOWELS, CONSONANTS
    ):
        sld = f"{c1}{v1}{c2}{v2}{c3}"
        if min_len <= len(sld) <= max_len and sld not in seen:
            seen.add(sld)
            candidates.append(sld)

    rng.shuffle(candidates)
    return candidates[:count]
