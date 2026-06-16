"""Storyboard vision gate — verify rendered stills against the creative brief.

Uses a vision model (gpt-4o-mini) to check each still for brand
compliance, readability, composition, and emotional impact before
the pipeline spends time on full rendering.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

from openai import OpenAI
from rich.console import Console

from crewai_remotion.config import get_settings
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.development import CreativeBrief
from crewai_remotion.models.visual_development import ComposedFrames

console = Console()

_STORYBOARD_VISION_MODEL = "gpt-4o-mini"

_CRITIQUE_PROMPT = (
    "You are a visual design critic for short-form social videos (TikTok/Reels style). "
    "You are reviewing storyboard still frames BEFORE a full video render. "
    "Analyze the attached image and answer EVERY question below with a PASS or FAIL "
    "plus one sentence of reasoning.\n\n"
    "Brand colors present? (primary + accent should be visible)\n"
    "Typography readable? (not clipped, good contrast against background)\n"
    "Composition matches layout intent? (headline placement, safe zones respected)\n"
    "Visual matches key message? (imagery supports the core idea)\n"
    "Hook attention-grabbing? (first frame should compel watching)\n"
    "CTA clear and actionable? (final frame should prompt action)\n\n"
    "Respond in this exact JSON format:\n"
    '{"brand_colors": {"pass": true/false, "reason": "..."}, '
    '"typography": {"pass": true/false, "reason": "..."}, '
    '"composition": {"pass": true/false, "reason": "..."}, '
    '"key_message": {"pass": true/false, "reason": "..."}, '
    '"hook": {"pass": true/false, "reason": "..."}, '
    '"cta": {"pass": true/false, "reason": "..."}, '
    '"overall_impression": "one-paragraph summary"}'
)



def _critique_one_still(
    image_path: Path,
    creative_brief: CreativeBrief | None,
    brand: BrandProfile | None,
    frame_label: str,
    key_message: str,
    cta_text: str,
) -> dict | None:
    """Send a single storyboard still to the vision model for critique.

    Returns parsed critique dict, or None if the call fails.
    """
    settings = get_settings()
    api_key = settings.openai_api_key
    if not api_key:
        return None

    image_bytes = image_path.read_bytes()
    b64_image = base64.b64encode(image_bytes).decode("utf-8")
    mime = "image/png"

    # Tailor the prompt slightly per frame
    frame_context = _CRITIQUE_PROMPT
    if "hook" in frame_label:
        frame_context += (
            f"\n\nContext: This is the HOOK/opening frame. "
            f"The key message is: \"{key_message}\""
        )
    elif "cta" in frame_label:
        frame_context += (
            f"\n\nContext: This is the CTA/closing frame. "
            f"The intended CTA is: \"{cta_text}\""
        )
    else:
        frame_context += (
            f"\n\nContext: This is a body frame from a video about: \"{key_message}\""
        )

    if brand:
        frame_context += (
            f"\n\nBrand context — primary color: {brand.visual.primary}, "
            f"accent: {brand.visual.accent}, brand name: {brand.name}"
        )

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model=_STORYBOARD_VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": frame_context},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime};base64,{b64_image}",
                                "detail": "high",
                            },
                        },
                    ],
                }
            ],
            max_tokens=800,
        )
    except Exception as exc:
        console.print(f"  [yellow]storyboard gate: vision API call failed: {exc}[/]")
        return None

    raw = (response.choices[0].message.content or "").strip()

    # Try to parse JSON from response

    try:
        # The model may wrap in markdown code fences
        if raw.startswith("```"):
            lines = raw.splitlines()
            raw = "\n".join(
                l for l in lines if not l.startswith("```")
            ).strip()
        return json.loads(raw)
    except json.JSONDecodeError:
        console.print(
            f"  [yellow]storyboard gate: could not parse JSON from vision response[/]"
        )
        return None


_CRITERIA_KEYS = [
    "brand_colors",
    "typography",
    "composition",
    "key_message",
    "hook",
    "cta",
]


def gate_storyboard(
    stills: list[Path],
    creative_brief: CreativeBrief | None = None,
    brand: BrandProfile | None = None,
    composed_frames: ComposedFrames | None = None,
) -> tuple[bool, str, dict]:
    """Verify storyboard frames visually against the creative brief.

    Returns (passed: bool, message: str, critique: dict).
    The critique dict maps frame labels to per-criterion results.

    Pass threshold: at least 4/6 criteria must pass on average across
    all stills.  Individual per-frame aggregation is softer — a single
    failing frame does not block if others compensate.
    """
    settings = get_settings()

    if not stills:
        return True, "No storyboard stills to verify", {}

    if not settings.openai_api_key:
        return (
            True,
            "OpenAI API key unavailable — skipping visual storyboard verification",
            {},
        )

    key_message = creative_brief.key_message if creative_brief else "unknown"
    cta_text = creative_brief.cta if creative_brief else ""

    all_frames_critique: dict = {}
    total_passes = 0
    total_checks = 0

    for still_path in stills:
        label = still_path.stem.split("_")[0]  # "hook", "body_1", "cta", etc.
        console.print(f"  [dim]storyboard gate: critiquing {label} ({still_path.name})[/]")

        result = _critique_one_still(
            still_path, creative_brief, brand, label, key_message, cta_text
        )

        if result is None:
            continue

        frame_criteria: dict = {}
        frame_passes = 0
        frame_checks = 0

        for key in _CRITERIA_KEYS:
            criterion = result.get(key)
            if isinstance(criterion, dict) and "pass" in criterion:
                frame_criteria[key] = criterion
                frame_checks += 1
                if criterion.get("pass"):
                    frame_passes += 1

        all_frames_critique[label] = {
            "criteria": frame_criteria,
            "overall": result.get("overall_impression", ""),
        }

        total_passes += frame_passes
        total_checks += frame_checks

    if total_checks == 0:
        return (
            True,
            "Storyboard verification did not produce any checkable results — skipping gate",
            all_frames_critique,
        )

    pass_ratio = total_passes / total_checks
    threshold = 4 / 6  # ~0.667

    if pass_ratio >= threshold:
        message = (
            f"Storyboard visual verification passed: "
            f"{total_passes}/{total_checks} criteria OK "
            f"({pass_ratio:.0%})"
        )
        return True, message, all_frames_critique

    message = (
        f"Storyboard visual issues detected: "
        f"{total_passes}/{total_checks} criteria OK "
        f"({pass_ratio:.0%}, threshold {threshold:.0%})"
    )
    return False, message, all_frames_critique
