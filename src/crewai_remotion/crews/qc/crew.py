from __future__ import annotations

import json

from crewai import Agent

from crewai_remotion.crews.llm import get_llm
from crewai_remotion.models.video_spec import VideoSpec
from crewai_remotion.models.visual_development import ComposedFrames
from crewai_remotion.models.writers_room import AVScript, ContinuityBible


def run_qc_crew(
    video_spec: VideoSpec,
    composed: ComposedFrames,
    continuity_bible: ContinuityBible,
    av_script: AVScript,
) -> dict:
    """QC: Script Supervisor pass 2 + Post Producer — final check before render."""
    llm = get_llm()

    spec_json = video_spec.model_dump_json()
    bible_json = continuity_bible.model_dump_json()

    # Script Supervisor pass 2
    from crewai_remotion.models.writers_room import ContinuityReport
    script_sup = Agent(
        role="Script Supervisor",
        goal="Compare ContinuityBible against VideoSpec + ComposedFrames — catch text/VO drift",
        backstory="Continuity specialist. You track every word, claim, and CTA across all departments. "
                  "Pass 1 was after Writers Room. Pass 2 compares final spec against bible.",
        llm=llm,
        verbose=True,
    )
    continuity: ContinuityReport = script_sup.kickoff(
        f"ContinuityBible: {bible_json}\n"
        f"VideoSpec headlines: {json.dumps([s.headline for s in video_spec.scenes])}\n"
        f"AVScript VO lines: {json.dumps([b.vo_line for b in av_script.beats])}\n"
        "Check: canonical_vo_lines match VideoSpec headlines (semantic match, not exact string), "
        "on_screen_text present in spec, claims consistent, CTA matches. "
        "Output issues list with severity and responsible_role.",
        response_format=ContinuityReport,
    ).pydantic

    # Post Producer
    from crewai_remotion.models.production_state import QCVerdict
    post_prod = Agent(
        role="Post Producer",
        goal="Final QC sign-off — schema check, smoke readiness, delivery approval",
        backstory="QC lead. You are the last human-like check before render. "
                  "You verify the spec is complete and render-ready.",
        llm=llm,
        verbose=True,
    )
    qc: QCVerdict = post_prod.kickoff(
        f"VideoSpec: {spec_json}\n"
        f"ComposedFrames: {composed.model_dump_json()}\n"
        "Check: all scenes have duration_frames > 0, headline present, "
        "theme tokens are valid hex colors, width=1080 height=1920, fps=30. "
        "Output passes=true and empty issues list if spec is render-ready. "
        "If issues found, list each with responsible_dept for routing.",
        response_format=QCVerdict,
    ).pydantic

    return {
        "continuity": continuity,
        "qc_verdict": qc,
    }
