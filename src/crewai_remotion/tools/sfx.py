from __future__ import annotations

from enum import Enum
import json
import shutil
from pathlib import Path
from typing import Any

from crewai_remotion.config import get_settings
from crewai_remotion.models.production_state import ProductionState
from crewai_remotion.models.video_spec import SfxCueSpec

# CDN base URL for @remotion/sfx built-in sounds.
# When a sound isn't available locally, we fall back to this CDN.
_SFX_CDN_BASE = "https://remotion.media/sfx"


def build_sfx_manifest() -> dict[str, Any]:
    """Read assets/sfx/manifest.json and return the full catalog."""
    settings = get_settings()
    manifest_path = settings.root / "assets" / "sfx" / "manifest.json"
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    return {"sfx": []}


def _lookup_sfx(sfx_id: str) -> dict[str, Any] | None:
    """Find an SFX entry in the manifest by id."""
    manifest = build_sfx_manifest()
    for entry in manifest.get("sfx", []):
        if entry.get("id") == sfx_id:
            return entry
    return None


def resolve_sfx_path(sfx_id: str) -> Path | None:
    """Resolve an SFX id to a local file path, if the file exists locally.

    Returns None for CDN-only sounds (those that lack a local file).
    """
    entry = _lookup_sfx(sfx_id)
    if not entry:
        return None
    settings = get_settings()
    local = settings.root / "assets" / "sfx" / entry.get("file", "")
    if local.exists():
        return local
    return None


def resolve_sfx_src(sfx_id: str, run_id: str) -> str | None:
    """Resolve an SFX id to a `src` string for Remotion.

    Local files are copied to remotion/public/runs/<id>/ and get a relative path.
    CDN-only sounds get a direct HTTPS URL.
    """
    entry = _lookup_sfx(sfx_id)
    if not entry:
        return None

    settings = get_settings()
    local = settings.root / "assets" / "sfx" / entry.get("file", "")
    if local.exists():
        # Will be copied by wire_sfx_to_spec; return the public-relative path
        return f"runs/{run_id}/{local.name}"

    # Fall back to CDN URL
    filename = entry.get("file", f"{sfx_id}.wav")
    return f"{_SFX_CDN_BASE}/{filename}"


def wire_sfx_to_spec(state: ProductionState) -> None:
    """After postproduction: copy needed SFX files and populate video_spec.audio.sfx.

    Converts SoundPlan.sfx_cues → video_spec.audio.sfx.cues, resolving
    each sfx_id to a proper src path.  Also handles backward compat:
    if sfx_cues is empty but sfx_on_cuts has entries, converts them.
    """
    if not state.video_spec:
        return

    sound_plan = state.sound_plan
    if not sound_plan:
        return

    settings = get_settings()
    run_id = state.run_id
    remotion_public = settings.root / "remotion" / "public" / "runs" / run_id
    remotion_public.mkdir(parents=True, exist_ok=True)

    cues: list[dict[str, Any]] = []

    # Primary: use sfx_cues if available
    if sound_plan.sfx_cues:
        for cue in sound_plan.sfx_cues:
            entry = _lookup_sfx(cue.sfx_id)
            if not entry:
                continue

            local = settings.root / "assets" / "sfx" / entry.get("file", "")
            if local.exists():
                dest = remotion_public / local.name
                if not dest.exists():
                    shutil.copy2(local, dest)
                src = f"runs/{run_id}/{local.name}"
            else:
                filename = entry.get("file", f"{cue.sfx_id}.wav")
                src = f"{_SFX_CDN_BASE}/{filename}"

            cues.append({
                "frame": cue.frame,
                "src": src,
                "volume": cue.volume,
                "cut_type": cue.cut_type,
            })
    # Backward compat: convert old sfx_on_cuts if no sfx_cues present
    elif sound_plan.sfx_on_cuts:
        # sfx_on_cuts lack frame info — derive from edit decision scene order
        edit_decisions = state.edit_decisions
        frame_by_cut: dict[str, int] = {}
        if edit_decisions and edit_decisions.decisions:
            accumulated = 0
            for scene in state.video_spec.scenes:
                cut = next(
                    (d for d in edit_decisions.decisions if d.scene_id == scene.id),
                    None,
                )
                if cut:
                    ct = cut.cut_type.value if isinstance(cut.cut_type, Enum) else str(cut.cut_type)
                    frame_by_cut[ct] = accumulated
                accumulated += scene.duration_frames

        for sfx_on_cut in sound_plan.sfx_on_cuts:
            sfx_id = sfx_on_cut.sfx
            if not sfx_id:
                continue
            entry = _lookup_sfx(sfx_id)
            if not entry:
                continue

            frame = frame_by_cut.get(sfx_on_cut.cut_type, 0)
            local = settings.root / "assets" / "sfx" / entry.get("file", "")
            if local.exists():
                dest = remotion_public / local.name
                if not dest.exists():
                    shutil.copy2(local, dest)
                src = f"runs/{run_id}/{local.name}"
            else:
                filename = entry.get("file", f"{sfx_id}.wav")
                src = f"{_SFX_CDN_BASE}/{filename}"

            cues.append({
                "frame": frame,
                "src": src,
                "volume": 0.7,
                "cut_type": sfx_on_cut.cut_type,
            })

    # Populate video_spec
    spec_cues = [
        SfxCueSpec(
            frame=c["frame"],
            src=c["src"],
            volume=c.get("volume", 0.7),
            cut_type=c.get("cut_type"),
        )
        for c in cues
    ]
    state.video_spec.audio.sfx.cues = spec_cues
