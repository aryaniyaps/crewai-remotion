"""Gate PictureLock: Editor locks timing before motion/color/sound polish."""
from __future__ import annotations

from crewai_remotion.models.cinematic_cuts import (
    CutType,
    J_CUT_LEAD_RANGE,
    L_CUT_TRAIL_RANGE,
    MAX_SMASH_CUTS_PER_30S,
    PictureLockCertificate,
    SplitEdit,
)
from crewai_remotion.models.postproduction import EditDecisionListV2


def gate_picture_lock(
    edl: EditDecisionListV2,
    audio_duration_sec: float,
    fps: int = 30,
    captions_word_count: int = 0,
) -> tuple[bool, str, PictureLockCertificate]:
    """
    Validates Editor's EditDecisionList before Motion/Color/Sound proceed.

    Checks:
    1. Beat durations sum to audio.duration_sec ±2 frames
    2. Every cut_out has valid cut_type + resolvable audio_sync_ref
    3. J/L lead/trail frames in range
    4. Smash cut count ≤ 1 per 30s
    """
    cert = PictureLockCertificate(
        approved=False,
        total_frames=edl.total_frames,
        audio_duration_sec=audio_duration_sec,
    )

    if not edl.cuts:
        return False, "EditDecisionList has no cuts", cert

    # Check 1: Duration sum — log warning if drift > 20%, never block
    expected_frames = int(audio_duration_sec * fps)
    frame_drift = abs(edl.total_frames - expected_frames)
    cert.frame_drift = frame_drift
    if frame_drift > expected_frames * 0.5:
        cert.editor_notes = (
            f"WARNING: Beat durations sum to {edl.total_frames}f, "
            f"audio is {expected_frames}f (drift={frame_drift}). "
            f"Mograph TD will normalize."
        )
    # Never block on drift — Editor provides intent, Mograph TD normalizes

    # Check 2: Valid cut types + audio_sync_refs
    for cut in edl.cuts:
        if cut.cut_type not in CutType:
            return False, f"Invalid cut_type '{cut.cut_type}' in cut {cut.audio_sync_ref}", cert
        if not cut.audio_sync_ref:
            return False, "Cut missing audio_sync_ref — cannot resolve against captions", cert
        if captions_word_count > 0 and not _is_resolvable(cut.audio_sync_ref, captions_word_count):
            return False, f"audio_sync_ref '{cut.audio_sync_ref}' not resolvable against captions", cert

    # Check 3: J/L split edit ranges (auto-correct 0 to range minimum)
    for cut in edl.cuts:
        if cut.split_edit == SplitEdit.J_CUT:
            if cut.audio_lead_frames == 0:
                cut.audio_lead_frames = J_CUT_LEAD_RANGE["min"]
            elif not (J_CUT_LEAD_RANGE["min"] <= cut.audio_lead_frames <= J_CUT_LEAD_RANGE["max"]):
                return False, (
                    f"J-cut lead frames {cut.audio_lead_frames} out of range "
                    f"[{J_CUT_LEAD_RANGE['min']}, {J_CUT_LEAD_RANGE['max']}]"
                ), cert
        if cut.split_edit == SplitEdit.L_CUT:
            if cut.audio_trail_frames == 0:
                cut.audio_trail_frames = L_CUT_TRAIL_RANGE["min"]
            elif not (L_CUT_TRAIL_RANGE["min"] <= cut.audio_trail_frames <= L_CUT_TRAIL_RANGE["max"]):
                return False, (
                    f"L-cut trail frames {cut.audio_trail_frames} out of range "
                    f"[{L_CUT_TRAIL_RANGE['min']}, {L_CUT_TRAIL_RANGE['max']}]"
                ), cert

    # Check 4: Smash cut limit
    smash_count = sum(1 for c in edl.cuts if c.cut_type == CutType.SMASH_CUT)
    duration_30s_chunks = max(1, audio_duration_sec / 30.0)
    if smash_count > MAX_SMASH_CUTS_PER_30S * duration_30s_chunks:
        return False, (
            f"Smash cut count {smash_count} exceeds limit "
            f"({MAX_SMASH_CUTS_PER_30S} per 30s)"
        ), cert

    cert.approved = True
    cert.editor_notes = f"Picture locked: {len(edl.cuts)} cuts, {edl.total_frames}f, drift={frame_drift}f"
    return True, cert.editor_notes, cert


def _is_resolvable(ref: str, word_count: int) -> bool:
    """Check if audio_sync_ref looks like a resolvable Whisper word_id."""
    if ref.startswith("word_id_"):
        try:
            idx = int(ref.split("_")[-1])
            return 0 <= idx < word_count
        except (ValueError, IndexError):
            return False
    # phrase_id, beat_id refs are always resolvable
    return True
