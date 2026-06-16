from __future__ import annotations

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from crewai_remotion.tools.serper_client import SerperError, image_search, web_search


class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query")


class ImageSearchInput(BaseModel):
    query: str = Field(..., description="Image search query")
    num: int = Field(5, description="Number of results")


class SerperWebSearchTool(BaseTool):
    name: str = "serper_web_search"
    description: str = "Search the web via Serper.dev for facts, angles, and sources about a topic."
    args_schema: type[BaseModel] = WebSearchInput

    def _run(self, query: str) -> str:
        try:
            brief = web_search(query)
            return brief.model_dump_json()
        except SerperError as exc:
            return f"ERROR: {exc}"


class SerperImageSearchTool(BaseTool):
    name: str = "serper_image_search"
    description: str = "Search Google Images via Serper.dev. Returns image URLs, titles, and dimensions."
    args_schema: type[BaseModel] = ImageSearchInput

    def _run(self, query: str, num: int = 5) -> str:
        try:
            results = image_search(query, num=num)
            return "[" + ",".join(r.model_dump_json() for r in results) + "]"
        except SerperError as exc:
            return f"ERROR: {exc}"
