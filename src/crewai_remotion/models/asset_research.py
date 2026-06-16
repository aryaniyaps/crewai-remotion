from __future__ import annotations

from pydantic import BaseModel, Field, HttpUrl


class ImageSearchResult(BaseModel):
    title: str = ""
    image_url: str
    source_url: str = ""
    width: int | None = None
    height: int | None = None


class SceneImageQuery(BaseModel):
    beat_id: str
    search_query: str
    visual_rationale: str = ""
    preferred_style: str = "photo"  # photo | logo | screenshot | abstract


class SceneImageAsset(BaseModel):
    beat_id: str
    local_path: str
    public_path: str  # path under remotion/public for staticFile()
    source_url: str
    alt_text: str = ""
    width: int | None = None
    height: int | None = None


class AssetResearchBrief(BaseModel):
    """Crew output: what to search for per scene."""
    scene_queries: list[SceneImageQuery] = Field(default_factory=list)
    brand_visual_notes: str = ""


class SceneImageManifest(BaseModel):
    """Resolved downloaded assets ready for VideoSpec."""
    assets: list[SceneImageAsset] = Field(default_factory=list)

    def for_beat(self, beat_id: str) -> SceneImageAsset | None:
        for a in self.assets:
            if a.beat_id == beat_id:
                return a
        return None
