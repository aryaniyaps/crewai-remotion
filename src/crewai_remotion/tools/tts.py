from __future__ import annotations

import struct
import wave
from pathlib import Path

from rich.console import Console

from crewai_remotion.models.production_state import ProductionState
from crewai_remotion.tools.piper_tts import DEFAULT_VOICE, synthesize_to_wav as piper_synthesize

console = Console()


def _script_text(state: ProductionState) -> str:
    if state.av_script:
        hook = state.av_script.hook.strip()
        beats = state.av_script.beats
        # Deduplicate: if first beat's vo_line matches the hook (common in
        # writers_room output where hook text populates both fields), skip it.
        if beats and beats[0].vo_line.strip() == hook:
            lines = [b.vo_line for b in beats]
        else:
            lines = [hook] + [b.vo_line for b in beats]
        return " ".join(lines)
    return state.effective_topic or state.topic


def _write_silent_wav(path: Path, duration_sec: float = 5.0, sample_rate: int = 24000) -> None:
    n_frames = int(duration_sec * sample_rate)
    with wave.open(str(path), "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<h", 0) * n_frames)


def _voice_name(state: ProductionState) -> str:
    if state.brand and state.brand.audio.voice:
        return state.brand.audio.voice
    from crewai_remotion.config import get_settings

    return get_settings().piper_voice or DEFAULT_VOICE


def generate_voiceover(state: ProductionState) -> tuple[Path, bool]:
    """Synthesize voiceover via the configured TTS provider. Returns (path, success)."""
    out = state.run_output()
    path = out / "voice.wav"
    text = _script_text(state)
    (out / "voice_script.txt").write_text(text, encoding="utf-8")

    provider = state.brand.audio.tts_provider if state.brand else "piper"
    clone_sample_raw: str | None = (
        state.brand.audio.tts_clone_sample if state.brand else None
    )
    clone_sample = Path(clone_sample_raw) if clone_sample_raw else None
    voice = _voice_name(state)

    try:
        _synthesize_with(provider, text, path, voice, clone_sample)
        console.print(f"[green]TTS:[/green] {provider} → {path.name}")
        return path, True
    except Exception as exc:
        err_path = out / "tts_error.txt"
        err_path.write_text(f"{type(exc).__name__}: {exc}\n", encoding="utf-8")
        console.print(
            f"[yellow]Warning:[/yellow] {provider} TTS failed ({exc}). "
            f"Details: {err_path}"
        )

        # Fall back to Piper for any provider failure.
        if provider != "piper":
            console.print("[yellow]Falling back to Piper TTS...[/yellow]")
            try:
                piper_synthesize(text, path, voice)
                console.print("[green]TTS:[/green] piper (fallback) → {path.name}")
                return path, True
            except Exception as piper_exc:
                console.print(
                    f"[yellow]Warning:[/yellow] Piper fallback also failed "
                    f"({piper_exc}). Using silent audio."
                )

        duration = state.duration_sec if state.duration_sec else 30.0
        _write_silent_wav(path, duration_sec=min(duration, 30.0))
        return path, False


def _synthesize_with(
    provider: str,
    text: str,
    output_path: Path,
    voice_name: str,
    clone_sample: Path | None,
) -> None:
    """Dispatch TTS to the configured provider."""
    if provider == "piper":
        piper_synthesize(text, output_path, voice_name)
    elif provider == "f5-tts":
        from crewai_remotion.tools.f5_tts import synthesize_to_wav as f5_synthesize

        f5_synthesize(text, output_path, clone_sample)
    elif provider == "elevenlabs":
        from crewai_remotion.tools.elevenlabs_tts import synthesize_to_wav as el_synthesize

        el_synthesize(text, output_path, clone_sample)
    else:
        raise ValueError(f"Unknown TTS provider: {provider!r}")
