from __future__ import annotations

import json
from pathlib import Path

from crewai_remotion.config import get_settings
from crewai_remotion.models.production_state import ProductionState


def attach_music(state: ProductionState) -> Path | None:
    settings = get_settings()
    manifest_path = settings.root / "assets" / "music" / "manifest.json"
    mood = state.brand.audio.music_mood if state.brand else "upbeat"
    out = state.run_output()
    meta = {"mood": mood, "track_id": None, "path": None}

    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        tracks = [t for t in manifest.get("tracks", []) if t.get("mood") == mood]
        if tracks:
            track = tracks[0]
            meta["track_id"] = track["id"]
            track_path = settings.root / track.get("file", track.get("path", ""))
            if track_path.exists():
                dest = out / "music.mp3"
                dest.write_bytes(track_path.read_bytes())
                meta["path"] = str(dest.name)

    (out / "music_meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    # Audio wiring to video_spec happens later in _wire_audio_to_spec
    if state.video_spec:
        state.video_spec.audio.music_path = meta.get("path", "")
        state.video_spec.audio.music_mood = mood
    return out / "music.mp3" if meta["path"] else None
