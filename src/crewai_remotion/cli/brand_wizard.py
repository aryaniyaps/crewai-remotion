from __future__ import annotations

import shutil
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from crewai_remotion.config import get_settings
from crewai_remotion.models.brand import (
    AudioConfig,
    BrandProfile,
    VisualConfig,
    VoiceConfig,
    brand_dir_for_slug,
    default_brand_path,
    save_brand,
)

console = Console()

TONE_CHOICES = ["bold", "witty", "calm", "premium", "playful", "direct", "warm", "technical"]
FONT_CHOICES = [
    "Inter",
    "Space Grotesk",
    "DM Sans",
    "Poppins",
    "Montserrat",
    "Outfit",
    "Sora",
    "Manrope",
]
PALETTE_PRESETS = {
    "1": ("#FF3366", "#1A1A2E", "#FFD700"),
    "2": ("#6366F1", "#0F172A", "#22D3EE"),
    "3": ("#10B981", "#111827", "#F59E0B"),
    "4": ("#EC4899", "#18181B", "#A78BFA"),
}
MOTION_CHOICES = {
    "snappy": "Quick cuts, punchy springs — TikTok energy",
    "smooth": "Ease-in-out, gentle holds — premium feel",
    "kinetic": "Overshoot, stagger, motion blur — high energy",
}
VOICE_CHOICES = [
    "en_US-lessac-medium",
    "en_US-amy-medium",
    "en_US-ryan-medium",
    "en_GB-alan-medium",
]
MOOD_CHOICES = ["upbeat", "calm", "dramatic"]


def _preview_colors(primary: str, secondary: str, accent: str) -> None:
    table = Table(show_header=False, box=None, padding=(0, 2))
    for label, color in [("Primary", primary), ("Secondary", secondary), ("Accent", accent)]:
        table.add_row(f"[{color}]████[/]", label, color)
    console.print(table)


def run_brand_wizard(
    *,
    slug_hint: str | None = None,
    existing: BrandProfile | None = None,
    inline: bool = True,
) -> tuple[BrandProfile, Path]:
    settings = get_settings()
    step = 1
    total = 8

    if not inline:
        console.print(Panel("Let's set up your brand (~2 min)", style="bold magenta"))

    name = existing.name if existing else typer.prompt(f"━━━ Brand setup ({step}/{total}) ━━━\nBrand name", default=slug_hint or "")
    profile = existing or BrandProfile(name=name)
    profile.name = name
    step += 1

    console.print(f"\n━━━ Brand setup ({step}/{total}) ━━━")
    console.print("Pick 2–3 tone words (comma-separated):")
    console.print(", ".join(TONE_CHOICES))
    tone_raw = typer.prompt("Tone", default=", ".join(profile.voice.tone[:3]))
    profile.voice = VoiceConfig(
        tone=[t.strip() for t in tone_raw.split(",") if t.strip()],
        avoid_words=profile.voice.avoid_words,
        hook_patterns=profile.voice.hook_patterns,
    )
    step += 1

    avoid = typer.prompt(f"\n━━━ Brand setup ({step}/{total}) ━━━\nWords to avoid (optional)", default=", ".join(profile.voice.avoid_words), show_default=bool(profile.voice.avoid_words))
    profile.voice.avoid_words = [w.strip() for w in avoid.split(",") if w.strip()]
    step += 1

    console.print(f"\n━━━ Brand setup ({step}/{total}) ━━━")
    console.print("Color palette — pick preset [1-4] or enter custom hex")
    for k, (p, s, a) in PALETTE_PRESETS.items():
        console.print(f"  {k}. {p} / {s} / {a}")
    preset = typer.prompt("Preset or 'custom'", default="1")
    if preset in PALETTE_PRESETS:
        primary, secondary, accent = PALETTE_PRESETS[preset]
    else:
        primary = typer.prompt("Primary hex", default=profile.visual.primary)
        secondary = typer.prompt("Secondary hex", default=profile.visual.secondary)
        accent = typer.prompt("Accent hex", default=profile.visual.accent)
    _preview_colors(primary, secondary, accent)
    profile.visual = VisualConfig(
        **{**profile.visual.model_dump(), "primary": primary, "secondary": secondary, "accent": accent}
    )
    step += 1

    console.print(f"\n━━━ Brand setup ({step}/{total}) ━━━")
    for i, f in enumerate(FONT_CHOICES, 1):
        console.print(f"  {i}. {f}")
    font_idx = typer.prompt("Heading + body font (number)", default="1")
    try:
        font = FONT_CHOICES[int(font_idx) - 1]
    except (ValueError, IndexError):
        font = profile.visual.font_heading
    profile.visual.font_heading = font
    profile.visual.font_body = font
    step += 1

    console.print(f"\n━━━ Brand setup ({step}/{total}) ━━━")
    for k, desc in MOTION_CHOICES.items():
        console.print(f"  {k}: {desc}")
    motion = typer.prompt("Motion style", default=profile.visual.motion_style)
    if motion in MOTION_CHOICES:
        profile.visual.motion_style = motion  # type: ignore[assignment]
    step += 1

    console.print(f"\n━━━ Brand setup ({step}/{total}) ━━━")
    console.print("Piper voices (local, open-source):")
    for v in VOICE_CHOICES:
        console.print(f"  • {v}")
    voice = typer.prompt("Piper TTS voice", default=profile.audio.voice)
    mood = typer.prompt(f"Music mood ({'/'.join(MOOD_CHOICES)})", default=profile.audio.music_mood)
    profile.audio = AudioConfig(**{**profile.audio.model_dump(), "voice": voice, "music_mood": mood})  # type: ignore[arg-type]
    step += 1

    logo_path_str = typer.prompt(
        f"\n━━━ Brand setup ({step}/{total}) ━━━\nLogo file path (optional, Enter to skip)",
        default="",
        show_default=False,
    )

    slug = profile.slug()
    brand_dir = brand_dir_for_slug(settings.root, slug)
    brand_dir.mkdir(parents=True, exist_ok=True)
    out_path = default_brand_path(settings.root, slug)

    if logo_path_str.strip():
        src = Path(logo_path_str.strip()).expanduser()
        if src.exists():
            dest = brand_dir / "logo.svg"
            shutil.copy2(src, dest)
            profile.assets.logo = str(dest.relative_to(settings.root))

    summary = Table(title="Brand summary")
    summary.add_column("Field")
    summary.add_column("Value")
    summary.add_row("Name", profile.name)
    summary.add_row("Slug", slug)
    summary.add_row("Tone", ", ".join(profile.voice.tone))
    summary.add_row("Colors", f"{profile.visual.primary} / {profile.visual.secondary}")
    summary.add_row("Font", profile.visual.font_heading)
    summary.add_row("Motion", profile.visual.motion_style)
    summary.add_row("Voice", profile.audio.voice)
    console.print(summary)

    if not typer.confirm("Save this brand?", default=True):
        raise typer.Abort()

    save_brand(profile, out_path)
    active = settings.brands_dir / ".active"
    active.parent.mkdir(parents=True, exist_ok=True)
    active.write_text(str(out_path.relative_to(settings.root)), encoding="utf-8")

    console.print(Panel(f"Brand saved → {out_path.relative_to(settings.root)}", style="green"))
    if inline:
        console.print("[bold]Continuing with your video…[/bold]")
    return profile, out_path
