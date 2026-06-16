from __future__ import annotations

from pathlib import Path

from crewai import Agent

from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.development import CreativeBrief
from crewai_remotion.models.writers_room import AVScript, HookSelection

_REFERENCES_DIR = Path(__file__).resolve().parent.parent.parent / "references"


def _load_scripting_ref() -> str:
    ref_path = _REFERENCES_DIR / "shortform_scripting.md"
    return ref_path.read_text(encoding="utf-8") if ref_path.exists() else ""


def run_writers_room(
    topic: str, brand: BrandProfile, brief: CreativeBrief, duration_sec: float
) -> tuple[HookSelection, AVScript]:
    llm = get_llm()
    scripting_ref = _load_scripting_ref()

    tone_list = ", ".join(brand.voice.tone)

    writer = Agent(
        role="Short-Form Scriptwriter & Retention Strategist",
        goal=(
            "Write TikTok/Reels-first scripts that hook in 0-3 seconds, maintain retention "
            "through pattern interrupts and curiosity loops, and drive action through clear CTAs. "
            "Every beat must earn the next second of attention — no filler, no marketing-speak."
        ),
        backstory=(
            "Top 1% short-form scriptwriter with 500M+ organic views across TikTok, Reels, and Shorts. "
            "You understand retention mechanics at a physiological level — pattern interrupts, "
            "open loops, curiosity gaps, and the dopamine rhythm that keeps thumbs from scrolling. "
            "You write conversationally and punchy, never marketing-speak. "
            "You know that if the first 3 seconds don't create a question in the viewer's mind, "
            "the video is dead. Your scripts match the brand voice while feeling native to the platform — "
            "like a smart friend who happens to know a lot, not a brand talking at people."
        ),
        llm=llm,
        verbose=True,
    )

    ref_block = f"\n\n# Short-form scripting reference\n{scripting_ref}" if scripting_ref else ""

    # ── Hook generation ──
    hooks = writer.kickoff(
        f"Topic: {topic}\n"
        f"Brief: {brief.key_message}\n"
        f"Brand tone: {tone_list}\n"
        f"{ref_block}\n\n"
        f"Generate 3 hook candidates for a {duration_sec}s vertical social video, then pick the best. "
        f"Use varied hook patterns (question, controversial take, surprising fact, relatable moment, pattern interrupt). "
        f"Each hook's on-screen text must be ≤ 8 words.",
        response_format=HookSelection,
    ).pydantic

    # ── Script generation with quality-retry loop ──
    max_retries = 2
    base_prompt = (
        f"Write a full AVScript for a {duration_sec}s vertical social video.\n"
        f"Topic: {topic}\n"
        f"Brief: {brief.key_message}\n"
        f"Selected hook: {hooks.selected_id}\n"
        f"Brand tone: {tone_list}\n"
        f"{ref_block}\n\n"
        f"Distribute time: hook ~3s, 2-3 body points ~6-8s each, optional rehook ~4s, cta ~4-5s. "
        f"For {duration_sec}s target 4-6 beats total. "
        f"Beat types: hook, point, stat, rehook, cta. approved=true.\n"
        f"Max 8 words on_screen_text per beat. Each beat needs visual_intent describing what viewer sees."
    )

    script: AVScript | None = None
    issues: list[str] = []
    for attempt in range(max_retries + 1):
        prompt = base_prompt if attempt == 0 else _build_corrective_prompt(base_prompt, issues)
        script = writer.kickoff(prompt, response_format=AVScript).pydantic
        issues = _check_script_quality(script, duration_sec)
        if not issues:
            break
        if attempt < max_retries:
            failed_detail = "; ".join(issues)
            writer.kickoff(
                f"Your last AVScript had these quality issues: {failed_detail}. "
                f"Internalize these rules before the next attempt.",
            )

    assert script is not None
    return hooks, script


def _check_script_quality(script: AVScript, duration_sec: float) -> list[str]:
    """Deterministic quality checks. Returns list of failure messages (empty = pass)."""
    issues: list[str] = []

    # Every beat must have a non-empty vo_line
    for b in script.beats:
        if not b.vo_line or not b.vo_line.strip():
            issues.append(f"Beat {b.beat_id}: empty vo_line")

    # Hook beat on_screen_text must be ≤ 8 words
    hook_beats = [b for b in script.beats if b.beat_type == "hook"]
    if hook_beats:
        hook_text = hook_beats[0].on_screen_text
        if hook_text:
            wc = len(hook_text.split())
            if wc > 8:
                issues.append(f"Hook on_screen_text: {wc} words (max 8)")
    else:
        issues.append("No hook beat found")

    # Beat count: 4-6 for 30s, scale proportionally for other durations
    if duration_sec <= 20:
        min_beats, max_beats = 3, 5
    elif duration_sec <= 45:
        min_beats, max_beats = 4, 6
    else:
        min_beats, max_beats = 5, 8

    if len(script.beats) < min_beats:
        issues.append(f"Too few beats: {len(script.beats)} (min {min_beats} for {duration_sec}s)")
    elif len(script.beats) > max_beats:
        issues.append(f"Too many beats: {len(script.beats)} (max {max_beats} for {duration_sec}s)")

    return issues


def _build_corrective_prompt(base: str, issues: list[str]) -> str:
    failed_detail = "\n".join(f"- {i}" for i in issues)
    return (
        f"{base}\n\n"
        f"# QUALITY ISSUES TO FIX (retry)\n"
        f"The previous output had these problems:\n{failed_detail}\n\n"
        f"Write a CORRECTED AVScript addressing every issue above. "
        f"Double-check: every beat has vo_line text, hook on-screen text ≤ 8 words, "
        f"and total beat count is in the target range for the video duration."
    )
