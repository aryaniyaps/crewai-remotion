from __future__ import annotations

from crewai import Agent

from crewai_remotion.crews._common import _load_reference
from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.brand import BrandProfile
from crewai_remotion.models.postproduction import VODirection
from crewai_remotion.models.writers_room import AVScript


def run_voice_director(script: AVScript, brand: BrandProfile) -> VODirection:
    """Voice Director annotates script for TTS — pace, emphasis, phrase boundaries."""
    llm = get_llm()
    audio_ref = _load_reference("audio_edit_sync.md")

    director = Agent(
        role="Voice Director",
        goal="Annotate AV script with pacing, emphasis words, pauses, and phrase boundaries for TTS",
        backstory=f"VO director on set. {audio_ref[:400]} "
                  "You mark where the voice talent should pause, emphasize, and breathe. "
                  "Your direction dramatically improves TTS quality.",
        llm=llm,
        verbose=True,
    )
    vo_direction: VODirection = director.kickoff(
        f"AVScript: {script.model_dump_json()}\n"
        f"Brand tone: {', '.join(brand.voice.tone)}\n"
        "Mark: pacing (conversational/urgent/calm), emphasis_words per beat (1-2 words), "
        "pause_after_ms (200-500ms between beats), energy (low/medium/high), "
        "phrase_boundaries with beat_id + phrase_end_frame_hint per beat.",
        response_format=VODirection,
    ).pydantic
    return vo_direction
