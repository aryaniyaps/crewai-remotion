from __future__ import annotations

import json
import shutil
from pathlib import Path

from crewai_remotion.models.postproduction import DeliveryManifest
from crewai_remotion.models.production_state import ProductionState


def package_delivery(state: ProductionState, video_path: Path) -> DeliveryManifest:
    out = state.run_output()
    deliverables = out / "deliverables"
    deliverables.mkdir(exist_ok=True)

    manifest = DeliveryManifest(
        run_id=state.run_id,
        video_path=str(video_path.relative_to(out)) if video_path.exists() else "",
        spec_path="video_spec.json",
        captions_path="captions.json" if (out / "captions.json").exists() else "",
        script_path="av_script.json" if (out / "av_script.json").exists() else "",
    )

    images_manifest = out / "scene_image_manifest.json"
    if images_manifest.exists():
        shutil.copy2(images_manifest, deliverables / images_manifest.name)

    assets_dir = out / "assets" / "images"
    if assets_dir.exists():
        dest_assets = deliverables / "images"
        dest_assets.mkdir(exist_ok=True)
        for img in assets_dir.glob("*"):
            if img.is_file():
                shutil.copy2(img, dest_assets / img.name)

    for key, rel in [
        ("video", manifest.video_path),
        ("spec", manifest.spec_path),
        ("captions", manifest.captions_path),
        ("script", manifest.script_path),
    ]:
        if rel:
            src = out / rel
            if src.exists():
                shutil.copy2(src, deliverables / src.name)

    (deliverables / "manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    (out / "delivery_manifest.json").write_text(json.dumps(manifest.model_dump(), indent=2), encoding="utf-8")
    return manifest
