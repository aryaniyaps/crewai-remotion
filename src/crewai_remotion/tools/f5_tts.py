from __future__ import annotations

import wave
from pathlib import Path

# ---------------------------------------------------------------------------
# Lazy-loaded F5TTS singleton
# ---------------------------------------------------------------------------
_tts: object | None = None


def _get_tts():
    """Return a cached F5TTS instance, creating one on first call."""
    global _tts
    if _tts is None:
        try:
            from f5_tts import F5TTS
        except ImportError as exc:
            msg = (
                "f5-tts is not installed. "
                "Install it with: pip install f5-tts>=0.3.0\n"
                "Or: uv pip install f5-tts>=0.3.0"
            )
            raise ImportError(msg) from exc

        # Prefer GPU; fall back to CPU.
        try:
            import torch

            device = "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            device = "cpu"

        _tts = F5TTS(device=device)
    return _tts


# ---------------------------------------------------------------------------
# Public API — matches Piper's signature with clone_sample_path replacing
# voice_name
# ---------------------------------------------------------------------------
def synthesize_to_wav(
    text: str,
    output_path: Path,
    clone_sample_path: Path | None = None,
) -> Path:
    """Synthesise speech with F5-TTS, optionally cloning a reference voice.

    Parameters
    ----------
    text : str
        The text to speak.
    output_path : Path
        Destination WAV file (16-bit mono).
    clone_sample_path : Path | None
        Path to a short (3–10 s) reference WAV for zero-shot voice cloning.
        When ``None`` a built-in default reference voice is used.

    Returns
    -------
    Path
        The ``output_path``.
    """
    tts = _get_tts()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    kwargs: dict[str, object] = {
        "text": text,
        "output_path": str(output_path),
    }

    if clone_sample_path is not None:
        if not clone_sample_path.exists():
            raise FileNotFoundError(f"Clone sample not found: {clone_sample_path}")
        kwargs["ref_audio"] = str(clone_sample_path)
        # ref_text is optional — F5TTS.generate will auto-transcribe if omitted.

    # F5TTS.generate returns a NumPy array; also writes the file when
    # output_path is supplied.
    audio = tts.generate(**kwargs)  # type: ignore[arg-type]

    # Ensure output is a proper 16-bit mono WAV.
    # F5TTS may write float32 — re-encode to int16 for downstream consumers.
    try:
        import numpy as np

        if isinstance(audio, np.ndarray):
            _write_int16_wav(output_path, audio)
    except ImportError:
        pass  # numpy not available; trust the written file.

    return output_path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _write_int16_wav(path: Path, audio: "np.ndarray", sample_rate: int = 24000) -> None:  # noqa: F821
    """Write a numpy array as 16-bit mono WAV, overwriting *path*."""
    import numpy as np

    # Normalise and clamp.
    peak = np.max(np.abs(audio))
    if peak > 0:
        audio = audio / peak * 0.95
    audio = np.clip(audio, -1.0, 1.0)
    samples = (audio * 32767).astype(np.int16)

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
