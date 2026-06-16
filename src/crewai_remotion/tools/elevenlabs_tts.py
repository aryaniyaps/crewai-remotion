from __future__ import annotations

import struct
import wave
from pathlib import Path

import httpx

from crewai_remotion.config import get_settings

# Pre-made ElevenLabs voice ID (Rachel — warm American female).
# Used when no clone sample is provided.
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"

_API_BASE = "https://api.elevenlabs.io"


def _api_key() -> str:
    key = get_settings().elevenlabs_api_key
    if not key:
        raise RuntimeError(
            "ELEVENLABS_API_KEY is not set. "
            "Add it to your .env file or environment."
        )
    return key


def _clone_voice(client: httpx.Client, sample_path: Path, voice_name: str) -> str:
    """Upload a reference sample, create a cloned voice, return its id."""
    api_key = _api_key()

    with open(sample_path, "rb") as fh:
        files = {"files": (sample_path.name, fh, "audio/wav")}
        data = {"name": voice_name, "labels": '{"source":"crewai-remotion"}'}

        resp = client.post(
            f"{_API_BASE}/v1/voices/add",
            headers={"xi-api-key": api_key},
            files=files,
            data=data,
            timeout=60.0,
        )

    if resp.status_code == 401:
        raise RuntimeError("ElevenLabs API: invalid API key (401).")
    if not resp.is_success:
        raise RuntimeError(
            f"ElevenLabs voice-clone request failed ({resp.status_code}): "
            f"{resp.text[:500]}"
        )

    voice_id: str = resp.json()["voice_id"]
    return voice_id


def _tts_request(
    client: httpx.Client,
    voice_id: str,
    text: str,
    output_path: Path,
) -> Path:
    """Send a TTS request, requesting raw 16-bit PCM, and wrap it in WAV."""
    api_key = _api_key()

    resp = client.post(
        f"{_API_BASE}/v1/text-to-speech/{voice_id}",
        headers={
            "xi-api-key": api_key,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "output_format": "pcm_24000",
            "voice_settings": {
                "stability": 0.60,
                "similarity_boost": 0.80,
            },
        },
        timeout=120.0,
    )

    if resp.status_code == 401:
        raise RuntimeError("ElevenLabs API: invalid API key (401).")

    if not resp.is_success:
        raise RuntimeError(
            f"ElevenLabs TTS request failed ({resp.status_code}): "
            f"{resp.text[:500]}"
        )

    # Wrap raw 16-bit mono PCM in a WAV container.
    pcm = resp.content
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(pcm)

    return output_path


def synthesize_to_wav(
    text: str,
    output_path: Path,
    clone_sample_path: Path | None = None,
) -> Path:
    """Synthesise 16-bit mono WAV via ElevenLabs with optional voice cloning.

    Parameters
    ----------
    text : str
        The text to speak.
    output_path : Path
        Destination WAV file (16-bit mono, 24 kHz).
    clone_sample_path : Path | None
        Path to a short reference WAV for voice cloning.
        When ``None`` a default ElevenLabs voice is used.

    Returns
    -------
    Path
        The ``output_path``.
    """
    api_key = _api_key()

    with httpx.Client(http2=True) as client:
        if clone_sample_path is not None:
            if not clone_sample_path.exists():
                raise FileNotFoundError(
                    f"Clone sample not found: {clone_sample_path}"
                )
            voice_id = _clone_voice(client, clone_sample_path, "crewai-remotion")
        else:
            voice_id = _DEFAULT_VOICE_ID

        return _tts_request(client, voice_id, text, output_path)
