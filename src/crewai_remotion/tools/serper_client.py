from __future__ import annotations

import httpx

from crewai_remotion.config import get_settings
from crewai_remotion.models.asset_research import ImageSearchResult
from crewai_remotion.models.development import TopicResearchBrief


class SerperError(RuntimeError):
    pass


def _headers() -> dict[str, str]:
    settings = get_settings()
    if not settings.serper_api_key:
        raise SerperError("SERPER_API_KEY is required for research. Set it in .env")
    return {"X-API-KEY": settings.serper_api_key, "Content-Type": "application/json"}


def web_search(query: str, *, num: int = 5) -> TopicResearchBrief:
    payload = {"q": query, "num": num}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post("https://google.serper.dev/search", headers=_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()

    angles: list[str] = []
    facts: list[str] = []
    sources: list[str] = []
    for item in data.get("organic", [])[:num]:
        title = item.get("title", "")
        snippet = item.get("snippet", "")
        link = item.get("link", "")
        if title:
            angles.append(title)
        if snippet:
            facts.append(snippet[:240])
        if link:
            sources.append(link)
    return TopicResearchBrief(refined_angles=angles, key_facts=facts, sources=sources)


def image_search(query: str, *, num: int = 5) -> list[ImageSearchResult]:
    payload = {"q": query, "num": num}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post("https://google.serper.dev/images", headers=_headers(), json=payload)
        resp.raise_for_status()
        data = resp.json()

    results: list[ImageSearchResult] = []
    for item in data.get("images", [])[:num]:
        url = item.get("imageUrl") or item.get("thumbnailUrl")
        if not url:
            continue
        results.append(
            ImageSearchResult(
                title=item.get("title", ""),
                image_url=url,
                source_url=item.get("link", ""),
                width=item.get("imageWidth"),
                height=item.get("imageHeight"),
            )
        )
    return results
