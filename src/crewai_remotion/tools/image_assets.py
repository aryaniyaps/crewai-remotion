from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

from crewai_remotion.config import get_settings
from crewai_remotion.models.asset_research import (
    AssetResearchBrief,
    ImageSearchResult,
    SceneImageAsset,
    SceneImageManifest,
    SceneImageQuery,
)
from crewai_remotion.models.production_state import ProductionState
from crewai_remotion.tools.serper_client import SerperError, image_search

_UNSPLASH_ACCESS_KEY = ""  # Set via env UNSPLASH_ACCESS_KEY


def _ext_from_url(url: str) -> str:
    path = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp", ".gif"):
        if path.endswith(ext):
            return ext.lstrip(".")
    return "jpg"


def download_image(url: str, dest: Path) -> tuple[int, int] | None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with httpx.Client(timeout=45.0, follow_redirects=True) as client:
        resp = client.get(url, headers={"User-Agent": "crewai-remotion/0.1"})
        resp.raise_for_status()
        dest.write_bytes(resp.content)
    try:
        with Image.open(dest) as img:
            return img.size
    except Exception:
        return None


def _score_image(r: ImageSearchResult, query: str = "") -> float:
    """Score an image result for quality filtering. Higher = better."""
    score = 0.0
    w, h = r.width or 0, r.height or 0

    # Prefer high-resolution images
    if w >= 1920:
        score += 3.0
    elif w >= 1080:
        score += 2.0
    elif w >= 720:
        score += 1.0

    # Prefer vertical or square images (9:16 content)
    if h > 0 and w > 0:
        ratio = h / w
        if 0.8 <= ratio <= 2.0:
            score += 2.0
        elif ratio < 0.5:  # very wide — poor fit
            score -= 2.0

    # Penalize tiny images
    if w < 400 or h < 400:
        score -= 5.0

    # Penalize slop markers
    title = r.title.lower()
    slop_markers = ["icon", "logo vector", "clipart", "stock vector", "illustration"]
    for marker in slop_markers:
        if marker in title:
            score -= 2.0

    # Boost for query relevance in title
    if query:
        query_words = set(query.lower().split())
        title_words = set(title.split())
        overlap = query_words & title_words
        score += min(len(overlap) * 0.5, 3.0)

    return score


def pick_best_image(
    results: list[ImageSearchResult],
    min_width: int = 400,
    query: str = "",
) -> ImageSearchResult | None:
    if not results:
        return None
    scored = [(r, _score_image(r, query)) for r in results]
    scored.sort(key=lambda x: x[1], reverse=True)
    for r, score in scored:
        if score > 0 and (r.width or 0) >= min_width:
            return r
    # Fallback: best by size
    ranked = sorted(results, key=lambda r: (r.width or 0, r.height or 0), reverse=True)
    for r in ranked:
        if r.width and r.width >= min_width:
            return r
    return ranked[0]


def _search_unsplash(query: str, num: int = 5) -> list[ImageSearchResult]:
    """Search Unsplash for high-quality, free-to-use images."""
    import os

    access_key = os.environ.get("UNSPLASH_ACCESS_KEY", _UNSPLASH_ACCESS_KEY)
    if not access_key:
        return []

    results: list[ImageSearchResult] = []
    try:
        with httpx.Client(timeout=20.0) as client:
            resp = client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": num, "orientation": "portrait"},
                headers={"Authorization": f"Client-ID {access_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
            for photo in data.get("results", []):
                urls = photo.get("urls", {})
                img_url = urls.get("regular") or urls.get("small")
                if not img_url:
                    continue
                results.append(
                    ImageSearchResult(
                        title=photo.get("alt_description") or photo.get("description") or query,
                        image_url=img_url,
                        source_url=photo.get("links", {}).get("html", "https://unsplash.com"),
                        width=photo.get("width", 1080),
                        height=photo.get("height", 1350),
                    )
                )
    except Exception:
        pass
    return results


def _remove_background(image_path: Path) -> Path | None:
    """Remove image background using rembg. Returns path to bg-removed PNG, or None."""
    try:
        from rembg import remove
    except ImportError:
        return None

    try:
        with Image.open(image_path) as img:
            img_rgba = img.convert("RGBA")
            output = remove(img_rgba)
        out_path = image_path.with_suffix(".nobg.png")
        output.save(out_path, "PNG")
        return out_path
    except Exception:
        return None


def _enhance_search_query(query: str, preferred_style: str = "photo") -> str:
    """Add quality signals to search queries for better results."""
    quality_tokens = {
        "photo": "high quality professional photography",
        "logo": "clean modern logo design",
        "screenshot": "app screenshot ui design",
        "abstract": "abstract digital art modern",
    }
    suffix = quality_tokens.get(preferred_style, quality_tokens["photo"])
    # Remove slop keywords that return low-quality results
    slop = ["free", "download", "wallpaper", "template"]
    for word in slop:
        query = query.replace(word, "")
    query = " ".join(query.split())  # normalize whitespace
    if len(query) < 80:
        query = f"{query} {suffix}"
    return query


def resolve_scene_images(
    state: ProductionState,
    brief: AssetResearchBrief,
    *,
    images_per_query: int = 5,
    remove_bg: bool = False,
) -> SceneImageManifest:
    out = state.run_output()
    assets_dir = out / "assets" / "images"
    public_run_dir = get_settings().root / "remotion" / "public" / "runs" / state.run_id
    public_run_dir.mkdir(parents=True, exist_ok=True)

    manifest = SceneImageManifest()
    for query in brief.scene_queries:
        results: list[ImageSearchResult] = []

        # Enhance query for quality
        enhanced_query = _enhance_search_query(query.search_query, query.preferred_style)

        # Primary: Google Images via Serper
        try:
            results = image_search(enhanced_query, num=images_per_query)
        except SerperError:
            pass

        # Fallback: Unsplash (high-quality, free-to-use)
        if len(results) < 2:
            try:
                unsplash_results = _search_unsplash(enhanced_query, num=images_per_query)
                results.extend(unsplash_results)
            except Exception:
                pass

        if not results:
            continue

        best = pick_best_image(results, query=enhanced_query)
        if not best:
            continue

        ext = _ext_from_url(best.image_url)
        filename = f"{query.beat_id}_{hashlib.md5(enhanced_query.encode()).hexdigest()[:8]}.{ext}"
        local_path = assets_dir / filename
        try:
            size = download_image(best.image_url, local_path)
        except Exception:
            continue
        if not local_path.exists():
            continue

        # Background removal (optional)
        bg_removed_path: Path | None = None
        if remove_bg:
            bg_removed_path = _remove_background(local_path)
            if bg_removed_path:
                local_path = bg_removed_path

        public_filename = local_path.name
        public_path = f"runs/{state.run_id}/{public_filename}"
        shutil.copy2(local_path, public_run_dir / public_filename)

        manifest.assets.append(
            SceneImageAsset(
                beat_id=query.beat_id,
                local_path=str(local_path.relative_to(out)),
                public_path=public_path,
                source_url=best.source_url or best.image_url,
                alt_text=best.title or query.search_query,
                width=size[0] if size else best.width,
                height=size[1] if size else best.height,
            )
        )

    (out / "scene_image_manifest.json").write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
    return manifest


def build_queries_from_script(state: ProductionState) -> AssetResearchBrief:
    """Fallback query builder when crew output unavailable."""
    queries: list[SceneImageQuery] = []
    if not state.av_script:
        return AssetResearchBrief(scene_queries=queries)
    for beat in state.av_script.beats:
        if beat.beat_type in ("point", "stat", "hook"):
            subject = beat.on_screen_text or beat.vo_line.split(".")[0]
            queries.append(
                SceneImageQuery(
                    beat_id=beat.beat_id,
                    search_query=f"{subject}",
                    visual_rationale=f"Visual for {beat.beat_type} beat",
                    preferred_style="logo" if beat.beat_type == "point" else "photo",
                )
            )
    return AssetResearchBrief(scene_queries=queries)
