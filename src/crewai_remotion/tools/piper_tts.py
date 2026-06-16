from __future__ import annotations

import re
import wave
from pathlib import Path

from piper import PiperVoice
from piper.download_voices import download_voice

from crewai_remotion.config import get_settings

PIPER_VOICE_RE = re.compile(
    r"^(?P<lang_family>[^-]+)_(?P<lang_region>[^-]+)-(?P<voice_name>[^-]+)-(?P<voice_quality>.+)$"
)
DEFAULT_VOICE = "en_US-lessac-medium"

# Legacy OpenAI voice ids → Piper voice
_LEGACY_VOICE_MAP: dict[str, str] = {
    "alloy": DEFAULT_VOICE,
    "echo": "en_US-lessac-medium",
    "fable": "en_GB-alan-medium",
    "onyx": "en_US-ryan-medium",
    "nova": "en_US-amy-medium",
    "shimmer": "en_US-kristin-medium",
}


def resolve_piper_voice(voice: str) -> str:
    voice = voice.strip()
    if PIPER_VOICE_RE.match(voice):
        return voice
    return _LEGACY_VOICE_MAP.get(voice.lower(), DEFAULT_VOICE)


def voice_data_dir() -> Path:
    settings = get_settings()
    return settings.root / settings.piper_data_dir


def ensure_voice_model(voice_name: str) -> Path:
    voice_name = resolve_piper_voice(voice_name)
    data_dir = voice_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    model_path = data_dir / f"{voice_name}.onnx"
    if not model_path.exists():
        download_voice(voice_name, data_dir)
    return model_path


def synthesize_to_wav(text: str, output_path: Path, voice_name: str) -> Path:
    voice_name = resolve_piper_voice(voice_name)
    model_path = ensure_voice_model(voice_name)
    data_dir = voice_data_dir()
    voice = PiperVoice.load(model_path, download_dir=data_dir)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        params_set = False
        for chunk in voice.synthesize(text):
            if not params_set:
                wf.setframerate(chunk.sample_rate)
                wf.setsampwidth(chunk.sample_width)
                wf.setnchannels(chunk.sample_channels)
                params_set = True
            wf.writeframes(chunk.audio_int16_bytes)

    return output_path
