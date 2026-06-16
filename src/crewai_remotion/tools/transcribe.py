from __future__ import annotations

from pathlib import Path

from crewai_remotion.models.production_state import ProductionState
from crewai_remotion.models.video_spec import CaptionSegment, CaptionWord


def _synthetic_captions(state: ProductionState) -> list[CaptionSegment]:
    segments: list[CaptionSegment] = []
    if not state.av_script:
        return segments
    cursor_ms = 0
    for beat in state.av_script.beats:
        words = beat.vo_line.split()
        if not words:
            continue
        dur_ms = int(beat.duration_hint_sec * 1000)
        word_ms = max(dur_ms // len(words), 120)
        caption_words = []
        for w in words:
            caption_words.append(CaptionWord(text=w, start_ms=cursor_ms, end_ms=cursor_ms + word_ms))
            cursor_ms += word_ms
        segments.append(CaptionSegment(words=caption_words))
    return segments


def transcribe_audio(audio_path: Path, state: ProductionState) -> list[CaptionSegment]:
    segments = _synthetic_captions(state)
    out = state.run_output() / "captions.json"
    import json

    out.write_text(json.dumps([s.model_dump() for s in segments], indent=2), encoding="utf-8")
    return segments
