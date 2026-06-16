"""Brand and SEO scoring heuristics for domain names."""

from __future__ import annotations

import re
from dataclasses import dataclass

COMMON_ENGLISH = {
    "tech",
    "data",
    "cloud",
    "soft",
    "ware",
    "labs",
    "corp",
    "group",
    "global",
    "digital",
    "media",
    "studio",
    "systems",
    "ventures",
    "holdings",
}

NEGATIVE_FRAGMENTS = {
    "pig",
    "poo",
    "pee",
    "ass",
    "sex",
    "damn",
    "hell",
    "die",
    "kill",
    "hate",
    "fart",
    "barf",
    "gag",
    "wow",
    "ash",
    "rub",
    "box",
    "tax",
    "fee",
    "buy",
    "sell",
    "cheap",
    "wiki",
    "test",
    "demo",
    "junk",
    "spam",
    "bot",
    "nft",
    "coin",
    "cash",
}

TRADEMARK_LIKE = {
    "apple",
    "sony",
    "google",
    "meta",
    "amazon",
    "microsoft",
    "oracle",
    "intel",
    "nvidia",
    "samsung",
    "ibm",
    "cisco",
    "adobe",
    "spotify",
    "netflix",
    "uber",
    "lyft",
    "stripe",
    "paypal",
    "tesla",
}

HARD_CLUSTERS = re.compile(r"[^aeiou]{4,}|[b-df-hj-np-tv-x-z]{3,}")
AMBIGUOUS = re.compile(r"(^[qxz])|([qxz]$)|(.)\1{2,}")
DOUBLE_LETTER = re.compile(r"(.)\1")

# Soft, familiar consonants that read well to a general audience.
FRIENDLY_CONSONANTS = set("lmnrstvb")
HARS_LETTERS = set("qxzj")


@dataclass(frozen=True)
class DomainAnalysis:
    sld: str
    brand_score: float
    seo_score: float
    total_score: float
    brand_notes: list[str]
    seo_notes: list[str]
    syllables: int
    acquisition: str


def count_syllables(word: str) -> int:
    word = word.lower()
    groups = re.findall(r"[aeiouy]+", word)
    return max(1, len(groups))


def has_double_letters(name: str) -> bool:
    """True when any identical letters sit back-to-back (e.g. tt, gg, ll)."""
    return bool(DOUBLE_LETTER.search(name.lower()))


def alternates_vowels_consonants(name: str) -> bool:
    """Check C/V alternation — the easiest public pronunciation pattern."""
    if len(name) < 2:
        return True
    prev_vowel: bool | None = None
    for ch in name.lower():
        is_vowel = ch in "aeiou"
        if prev_vowel is not None and is_vowel == prev_vowel:
            return False
        prev_vowel = is_vowel
    return True


def analyze_sld(
    sld: str,
    *,
    price_usd: float,
    source: str,
    premium: bool = False,
) -> DomainAnalysis | None:
    name = sld.lower().strip()
    if not re.fullmatch(r"[a-z]+", name):
        return None
    if has_double_letters(name):
        return None

    brand_notes: list[str] = []
    seo_notes: list[str] = []
    brand = 100.0
    seo = 100.0

    length = len(name)
    if length < 4 or length > 7:
        return None

    if length <= 4:
        brand += 8
        seo += 10
        brand_notes.append("Ultra-short (4 letters) — Sony-tier length.")
    elif length == 5:
        brand += 6
        seo += 8
        brand_notes.append("Short 5-letter name — Apple-tier length.")
    elif length == 6:
        brand += 2
        seo += 4
    else:
        brand -= 8
        seo -= 6
        brand_notes.append("7 letters is acceptable but less iconic.")

    vowels = sum(ch in "aeiou" for ch in name)
    consonants = length - vowels
    ratio = vowels / length
    if ratio < 0.25 or ratio > 0.65:
        brand -= 18
        seo -= 10
        brand_notes.append("Vowel/consonant balance hurts pronounceability.")
    else:
        brand_notes.append("Balanced vowels — easy to pronounce globally.")

    if alternates_vowels_consonants(name):
        brand += 10
        brand_notes.append("Alternating vowel/consonant flow — natural to say aloud.")
    else:
        brand -= 12
        brand_notes.append("Clustered vowels/consonants — less intuitive for the public.")

    friendly = sum(ch in FRIENDLY_CONSONANTS for ch in name if ch not in "aeiou")
    harsh = sum(ch in HARS_LETTERS for ch in name)
    brand += min(8, friendly * 2)
    brand -= harsh * 8
    if friendly >= 2 and harsh == 0:
        brand_notes.append("Soft, familiar letter shapes — broad public appeal.")
    if harsh:
        brand_notes.append("Rare letters (q/x/z) make spelling and recall harder.")
    if name.endswith("j") or name.startswith("j"):
        brand -= 10
        brand_notes.append("'J' is easy to mishear as soft-g — weaker for mass-market recall.")

    syllables = count_syllables(name)
    if syllables == 2:
        brand += 8
        seo += 4
        brand_notes.append("Two syllables — strong recall pattern.")
    elif syllables == 1:
        brand += 4
    elif syllables >= 3:
        brand -= 10
        seo -= 6
        brand_notes.append("Three+ syllables — harder to say in one breath.")

    if HARD_CLUSTERS.search(name):
        brand -= 22
        seo -= 12
        brand_notes.append("Harsh consonant cluster reduces brand polish.")

    if AMBIGUOUS.search(name):
        brand -= 12
        seo -= 8
        seo_notes.append("Spelling/typing friction from rare letters or repeats.")

    bad_fragments = [frag for frag in NEGATIVE_FRAGMENTS if frag in name]
    if bad_fragments:
        brand -= 18 + min(12, 3 * len(bad_fragments))
        seo -= 8
        brand_notes.append(
            f"Contains awkward fragment(s): {', '.join(sorted(set(bad_fragments)))}."
        )

    if name.endswith(("a", "e", "o", "on", "ra", "va", "io")):
        brand += 6
        brand_notes.append("Open ending — smooth, memorable finish for a mass-market brand.")
    elif name.endswith(("i", "y")):
        brand += 3
        brand_notes.append("Light vowel ending — still approachable.")

    if name in TRADEMARK_LIKE or any(name.startswith(t) for t in TRADEMARK_LIKE):
        brand -= 35
        brand_notes.append("Too close to a famous brand — legal/confusion risk.")

    if name in COMMON_ENGLISH:
        brand -= 10
        seo -= 5
        brand_notes.append("Generic tech word — less distinctive as a parent brand.")

    if premium:
        brand -= 15
        seo -= 10
        brand_notes.append("Premium tier — exceeds typical startup budget.")

    if price_usd <= 11.5:
        seo += 6
        seo_notes.append("Standard .com registration pricing (~$11).")
    elif price_usd <= 20:
        seo += 2
        seo_notes.append("Within your $20 budget via marketplace/reseller listing.")
    else:
        brand -= 20
        seo -= 25
        seo_notes.append("Over budget.")

    # SEO fundamentals for a parent company domain.
    seo_notes.append(".com TLD — highest trust and type-in behavior.")
    seo_notes.append("No hyphens or numbers — clean brand SERP footprint.")
    if length <= 5:
        seo_notes.append("Short domains earn better direct traffic and lower typo rates.")

    brand = max(0.0, min(100.0, brand))
    seo = max(0.0, min(100.0, seo))
    total = round(brand * 0.55 + seo * 0.45, 2)

    acquisition = source
    if source == "registration" and price_usd <= 20:
        acquisition = "Buy now (standard registration)"
    elif source == "marketplace":
        acquisition = "Buy now (Porkbun marketplace listing)"

    return DomainAnalysis(
        sld=name,
        brand_score=round(brand, 2),
        seo_score=round(seo, 2),
        total_score=total,
        brand_notes=brand_notes,
        seo_notes=seo_notes,
        syllables=syllables,
        acquisition=acquisition,
    )
