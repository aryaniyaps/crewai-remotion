from __future__ import annotations

import html
import math
from pathlib import Path

from crewai_remotion.config import get_settings
from crewai_remotion.models.production_state import ProductionState
from crewai_remotion.models.video_spec import (
    GeneratedAssetConnection,
    GeneratedAssetElement,
    GeneratedAssetSpec,
    SceneSpec,
)

_CANVAS_W = 900
_CANVAS_H = 680


def generate_scene_assets(state: ProductionState) -> None:
    """Materialize model-authored scene asset specs into run-local SVGs.

    The LLM decides *what* to visualize via ``SceneSpec.generated_asset``.
    This function only turns that graph of elements/connections into a polished,
    deterministic SVG that Remotion can animate at render time.
    """
    if not state.video_spec:
        return

    settings = get_settings()
    public_dir = settings.root / "remotion" / "public" / "runs" / state.run_id / "generated"
    public_dir.mkdir(parents=True, exist_ok=True)

    for scene in state.video_spec.scenes:
        spec = _ensure_connected(scene.generated_asset or _fallback_asset_spec(scene))
        scene.generated_asset = spec
        svg = _render_svg(spec, scene)
        path = public_dir / f"{_safe_slug(scene.id)}.svg"
        path.write_text(svg, encoding="utf-8")
        scene.generated_asset_path = f"runs/{state.run_id}/generated/{path.name}"


def _ensure_connected(spec: GeneratedAssetSpec) -> GeneratedAssetSpec:
    """Guarantee the generated visual is a connected diagram, not isolated icons."""
    if len(spec.elements) < 2:
        return spec

    existing = {(c.from_id, c.to_id) for c in spec.connections}
    connections = list(spec.connections)
    subject = next((e for e in spec.elements if e.emphasis == "high" or e.role == "subject"), spec.elements[0])
    for element in spec.elements:
        if element.id == subject.id:
            continue
        if (subject.id, element.id) in existing or (element.id, subject.id) in existing:
            continue
        descriptor = f"{element.kind} {element.label} {element.role}".lower()
        flow = "power" if any(token in descriptor for token in ("power", "grid", "energy", "electric")) else "data"
        label = "powers" if flow == "power" else "feeds"
        connections.append(
            GeneratedAssetConnection(
                from_id=subject.id,
                to_id=element.id,
                label=label,
                flow=flow,
            )
        )
    return spec.model_copy(update={"connections": connections})


def _fallback_asset_spec(scene: SceneSpec) -> GeneratedAssetSpec:
    subject = scene.illustration_id or scene.headline or scene.type
    tokens = [t for t in subject.replace("_", " ").split() if t]
    root_label = " ".join(tokens[:3]).title() or "Core Idea"
    elements = [
        GeneratedAssetElement(id="core", kind=_kind_from_text(subject), label=root_label, role="subject", emphasis="high", x=0.44, y=0.52),
        GeneratedAssetElement(id="context", kind="node", label=(scene.subhead or scene.type or "context")[:22], role="context", emphasis="medium", x=0.78, y=0.36),
        GeneratedAssetElement(id="impact", kind="node", label="impact", role="outcome", emphasis="medium", x=0.74, y=0.68),
    ]
    connections = [
        GeneratedAssetConnection(from_id="core", to_id="context", label="drives", flow="data"),
        GeneratedAssetConnection(from_id="core", to_id="impact", label="shifts", flow="power"),
    ]
    return GeneratedAssetSpec(
        style="editorial_vector",
        subject=root_label,
        visual_metaphor=scene.headline,
        elements=elements,
        connections=connections,
        motion_notes="Primary generated vector asset from scene semantics.",
    )


def _render_svg(spec: GeneratedAssetSpec, scene: SceneSpec) -> str:
    theme = scene.generated_asset.style if scene.generated_asset else "editorial_vector"
    del theme  # style is model-authored metadata; colors come from VideoSpec theme in Remotion backdrop.

    elements = _with_positions(spec.elements)
    element_by_id = {e.id: e for e in elements}
    title = html.escape(spec.subject[:58])
    metaphor = html.escape(spec.visual_metaphor[:80])

    connection_svg = "\n".join(_connection_svg(c, element_by_id, i) for i, c in enumerate(spec.connections))
    element_svg = "\n".join(_element_svg(e, i) for i, e in enumerate(elements))
    particles = "\n".join(_particle_svg(i) for i in range(18))

    return f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"{_CANVAS_W}\" height=\"{_CANVAS_H}\" viewBox=\"0 0 {_CANVAS_W} {_CANVAS_H}\">
  <defs>
    <filter id=\"glow\" x=\"-40%\" y=\"-40%\" width=\"180%\" height=\"180%\">
      <feGaussianBlur stdDeviation=\"7\" result=\"blur\"/>
      <feMerge><feMergeNode in=\"blur\"/><feMergeNode in=\"SourceGraphic\"/></feMerge>
    </filter>
    <linearGradient id=\"panel\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"1\">
      <stop offset=\"0\" stop-color=\"#16172B\"/>
      <stop offset=\"1\" stop-color=\"#0B0D19\"/>
    </linearGradient>
    <linearGradient id=\"flowData\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"0\">
      <stop offset=\"0\" stop-color=\"#39E508\" stop-opacity=\"0\"/>
      <stop offset=\"0.5\" stop-color=\"#39E508\" stop-opacity=\"0.95\"/>
      <stop offset=\"1\" stop-color=\"#39E508\" stop-opacity=\"0\"/>
    </linearGradient>
    <linearGradient id=\"flowPower\" x1=\"0\" y1=\"0\" x2=\"1\" y2=\"0\">
      <stop offset=\"0\" stop-color=\"#FFD400\" stop-opacity=\"0\"/>
      <stop offset=\"0.5\" stop-color=\"#FFD400\" stop-opacity=\"0.95\"/>
      <stop offset=\"1\" stop-color=\"#FF2E6F\" stop-opacity=\"0\"/>
    </linearGradient>
  </defs>
  <rect x=\"30\" y=\"30\" width=\"840\" height=\"600\" rx=\"58\" fill=\"url(#panel)\" opacity=\"0.93\"/>
  <rect x=\"30\" y=\"30\" width=\"840\" height=\"600\" rx=\"58\" fill=\"none\" stroke=\"#FFFFFF\" stroke-opacity=\"0.13\" stroke-width=\"3\"/>
  <g opacity=\"0.48\">{particles}</g>
  <text x=\"66\" y=\"82\" fill=\"#F8F8FF\" font-family=\"Inter, Arial, sans-serif\" font-size=\"34\" font-weight=\"800\" letter-spacing=\"0.2\">{title}</text>
  <text x=\"68\" y=\"120\" fill=\"#B8B9C7\" font-family=\"Inter, Arial, sans-serif\" font-size=\"18\" font-weight=\"600\">{metaphor}</text>
  <g>{connection_svg}</g>
  <g>{element_svg}</g>
</svg>"""


def _with_positions(elements: list[GeneratedAssetElement]) -> list[GeneratedAssetElement]:
    if not elements:
        return [GeneratedAssetElement(id="core", kind="node", label="Core idea", emphasis="high", x=0.5, y=0.52)]

    count = len(elements)
    positioned: list[GeneratedAssetElement] = []
    for i, e in enumerate(elements):
        nx = _normalize_coord(e.x, _CANVAS_W)
        ny = _normalize_coord(e.y, _CANVAS_H)
        if nx is not None and ny is not None:
            positioned.append(e.model_copy(update={"x": nx, "y": ny}))
            continue
        angle = -math.pi / 2 + (2 * math.pi * i / max(count, 1))
        radius_x = 0.24 if e.emphasis != "high" else 0.05
        radius_y = 0.22 if e.emphasis != "high" else 0.03
        x = 0.5 + math.cos(angle) * radius_x
        y = 0.52 + math.sin(angle) * radius_y
        positioned.append(e.model_copy(update={"x": max(0.16, min(0.84, x)), "y": max(0.22, min(0.82, y))}))
    return _spread_positions(positioned)


def _normalize_coord(value: float | None, canvas_size: int) -> float | None:
    if value is None:
        return None
    # Model may output normalized 0-1, percentages 0-100, or SVG pixels.
    if 0 <= value <= 1:
        normalized = value
    elif 1 < value <= 100:
        normalized = value / 100
    else:
        normalized = value / canvas_size
    return max(0.14, min(0.86, normalized))


def _spread_positions(elements: list[GeneratedAssetElement]) -> list[GeneratedAssetElement]:
    """Prevent model-authored coordinates from collapsing elements into each other."""
    spread = list(elements)
    for i, current in enumerate(spread):
        x = current.x or 0.5
        y = current.y or 0.5
        for j, previous in enumerate(spread[:i]):
            px = previous.x or 0.5
            py = previous.y or 0.5
            dx = x - px
            dy = y - py
            if (dx * dx + dy * dy) ** 0.5 < 0.20:
                angle = -math.pi / 3 + (i + j) * 0.9
                x = max(0.18, min(0.82, x + math.cos(angle) * 0.18))
                y = max(0.24, min(0.78, y + math.sin(angle) * 0.16))
        spread[i] = current.model_copy(update={"x": x, "y": y})
    return spread


def _element_svg(e: GeneratedAssetElement, index: int) -> str:
    x = int((e.x or 0.5) * _CANVAS_W)
    y = int((e.y or 0.5) * _CANVAS_H)
    label = html.escape(e.label[:26])
    kind = e.kind.lower().replace("-", "_")
    scale = 1.18 if e.emphasis == "high" else 1.0 if e.emphasis == "medium" else 0.86
    body = _primitive_svg(kind, label)
    return f"""<g transform=\"translate({x} {y}) scale({scale})\" filter=\"url(#glow)\">
  {body}
  <text x=\"0\" y=\"96\" text-anchor=\"middle\" fill=\"#F8F8FF\" font-family=\"Inter, Arial, sans-serif\" font-size=\"22\" font-weight=\"800\">{label}</text>
</g>"""


def _primitive_svg(kind: str, label: str) -> str:
    del label
    if any(k in kind for k in ("server", "rack", "data_center", "datacenter")):
        return """<rect x=\"-92\" y=\"-74\" width=\"184\" height=\"142\" rx=\"24\" fill=\"#101426\" stroke=\"#FF2E6F\" stroke-opacity=\"0.75\" stroke-width=\"4\"/>
  <g fill=\"#39E508\"><circle cx=\"-58\" cy=\"-38\" r=\"8\"/><circle cx=\"-58\" cy=\"0\" r=\"8\"/><circle cx=\"-58\" cy=\"38\" r=\"8\"/></g>
  <g stroke=\"#FFD400\" stroke-width=\"8\" stroke-linecap=\"round\"><line x1=\"-32\" y1=\"-38\" x2=\"58\" y2=\"-38\"/><line x1=\"-32\" y1=\"0\" x2=\"58\" y2=\"0\"/><line x1=\"-32\" y1=\"38\" x2=\"58\" y2=\"38\"/></g>"""
    if any(k in kind for k in ("building", "city", "country", "nation")):
        return """<g><rect x=\"-98\" y=\"-60\" width=\"56\" height=\"130\" rx=\"8\" fill=\"#111527\" stroke=\"#FF2E6F\" stroke-width=\"4\"/><rect x=\"-28\" y=\"-100\" width=\"66\" height=\"170\" rx=\"8\" fill=\"#171B32\" stroke=\"#FFD400\" stroke-width=\"4\"/><rect x=\"54\" y=\"-36\" width=\"56\" height=\"106\" rx=\"8\" fill=\"#101426\" stroke=\"#39E508\" stroke-width=\"4\"/></g>"""
    if any(k in kind for k in ("power", "grid", "tower", "electric")):
        return """<g stroke-linecap=\"round\"><polygon points=\"0,-104 74,78 -74,78\" fill=\"#111527\" stroke=\"#FF2E6F\" stroke-width=\"5\"/><path d=\"M-116,-18 H116 M-92,28 H92 M-58,78 H58\" stroke=\"#39E508\" stroke-width=\"9\"/><circle cx=\"0\" cy=\"-104\" r=\"18\" fill=\"#FFD400\"/></g>"""
    if any(k in kind for k in ("chip", "gpu", "processor", "circuit")):
        return """<g><rect x=\"-74\" y=\"-74\" width=\"148\" height=\"148\" rx=\"26\" fill=\"#111527\" stroke=\"#FFD400\" stroke-width=\"5\"/><rect x=\"-34\" y=\"-34\" width=\"68\" height=\"68\" rx=\"14\" fill=\"#FF2E6F\"/><g stroke=\"#39E508\" stroke-width=\"8\" stroke-linecap=\"round\"><line x1=\"-118\" y1=\"-42\" x2=\"-78\" y2=\"-42\"/><line x1=\"78\" y1=\"-42\" x2=\"118\" y2=\"-42\"/><line x1=\"-118\" y1=\"42\" x2=\"-78\" y2=\"42\"/><line x1=\"78\" y1=\"42\" x2=\"118\" y2=\"42\"/></g></g>"""
    if any(k in kind for k in ("node", "connection", "data_flow", "stream")):
        return """<g fill="none" stroke-linecap="round"><circle cx="0" cy="0" r="64" fill="#111527" stroke="#39E508" stroke-width="5"/><circle cx="0" cy="0" r="18" fill="#39E508"/><path d="M-92,-44 C-44,-74 40,-74 92,-44 M-92,44 C-44,74 40,74 92,44" stroke="#AEB0C0" stroke-opacity="0.55" stroke-width="5"/><g fill="#FFD400"><circle cx="-82" cy="-42" r="10"/><circle cx="82" cy="-42" r="10"/><circle cx="-82" cy="42" r="10"/><circle cx="82" cy="42" r="10"/></g></g>"""
    if any(k in kind for k in ("chart", "graph", "stat", "statistics", "annotation")):
        return """<g><rect x="-92" y="-70" width="184" height="140" rx="24" fill="#111527" stroke="#FFD400" stroke-width="5"/><g stroke-linecap="round" stroke-width="12"><line x1="-52" y1="42" x2="-52" y2="-4" stroke="#39E508"/><line x1="0" y1="42" x2="0" y2="-42" stroke="#FF2E6F"/><line x1="52" y1="42" x2="52" y2="-22" stroke="#FFD400"/></g><path d="M-62,-18 C-24,-50 10,-2 62,-44" fill="none" stroke="#AEB0C0" stroke-width="5" stroke-linecap="round"/></g>"""
    if any(k in kind for k in ("arrow", "direction", "link")):
        return """<g fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M-100,0 H78" stroke="#39E508" stroke-width="18"/><path d="M38,-46 L96,0 L38,46" stroke="#FFD400" stroke-width="18"/><circle cx="-82" cy="0" r="18" fill="#FF2E6F" stroke="none"/></g>"""
    if any(k in kind for k in ("device", "phone", "smartphone", "screen")):
        return """<g><rect x="-62" y="-102" width="124" height="204" rx="30" fill="#111527" stroke="#FF2E6F" stroke-width="5"/><rect x="-44" y="-72" width="88" height="132" rx="14" fill="#171B32"/><circle cx="0" cy="78" r="9" fill="#39E508"/><path d="M-28,-34 H28 M-28,2 H28 M-28,38 H12" stroke="#FFD400" stroke-width="8" stroke-linecap="round"/></g>"""
    if any(k in kind for k in ("globe", "network", "internet", "fiber", "traffic")):
        return """<g fill=\"none\" stroke-linecap=\"round\"><circle cx=\"0\" cy=\"0\" r=\"82\" stroke=\"#FF2E6F\" stroke-width=\"5\"/><ellipse cx=\"0\" cy=\"0\" rx=\"38\" ry=\"82\" stroke=\"#AEB0C0\" stroke-width=\"4\"/><path d=\"M-82,0 Q0,-36 82,0 M-82,0 Q0,36 82,0\" stroke=\"#39E508\" stroke-width=\"8\"/><g fill=\"#FFD400\" stroke=\"none\"><circle cx=\"-72\" cy=\"-18\" r=\"13\"/><circle cx=\"62\" cy=\"-32\" r=\"13\"/><circle cx=\"20\" cy=\"60\" r=\"13\"/></g></g>"""
    if any(k in kind for k in ("cloud", "ai")):
        return """<path d=\"M-78,20 C-108,18 -118,-18 -92,-34 C-86,-78 -28,-86 -8,-52 C22,-88 82,-62 78,-18 C112,-14 112,30 76,34 H-72 C-96,34 -102,22 -78,20Z\" fill=\"#FFD400\" stroke=\"#FFFFFF\" stroke-opacity=\"0.26\" stroke-width=\"5\"/>"""
    return """<g><rect x=\"-90\" y=\"-70\" width=\"180\" height=\"140\" rx=\"34\" fill=\"#111527\" stroke=\"#FF2E6F\" stroke-width=\"5\"/><circle cx=\"-38\" cy=\"-10\" r=\"42\" fill=\"#FF2E6F\"/><rect x=\"18\" y=\"-48\" width=\"70\" height=\"70\" rx=\"16\" fill=\"#FFD400\"/><path d=\"M-34,56 Q8,16 54,54\" fill=\"none\" stroke=\"#39E508\" stroke-width=\"10\" stroke-linecap=\"round\"/></g>"""


def _connection_svg(c: GeneratedAssetConnection, by_id: dict[str, GeneratedAssetElement], index: int) -> str:
    a = by_id.get(c.from_id)
    b = by_id.get(c.to_id)
    if not a or not b:
        return ""
    x1, y1 = int((a.x or 0.5) * _CANVAS_W), int((a.y or 0.5) * _CANVAS_H)
    x2, y2 = int((b.x or 0.5) * _CANVAS_W), int((b.y or 0.5) * _CANVAS_H)
    cx = (x1 + x2) // 2
    cy = min(y1, y2) - 70 - (index % 3) * 20
    flow = "url(#flowPower)" if c.flow.lower() in {"power", "energy", "money", "influence"} else "url(#flowData)"
    label = html.escape(c.label[:20])
    label_y = max(cy - 12, 168)
    label_bg_w = max(54, min(170, 12 * len(label) + 22))
    label_svg = (
        f"<g opacity=\"0.92\"><rect x=\"{cx - label_bg_w // 2}\" y=\"{label_y - 19}\" "
        f"width=\"{label_bg_w}\" height=\"25\" rx=\"12\" fill=\"#0B0D19\" fill-opacity=\"0.78\"/>"
        f"<text x=\"{cx}\" y=\"{label_y}\" text-anchor=\"middle\" fill=\"#D8D9E6\" "
        f"font-family=\"Inter, Arial, sans-serif\" font-size=\"15\" font-weight=\"800\">{label}</text></g>"
    ) if label else ""
    return f"""<path d=\"M{x1},{y1} Q{cx},{cy} {x2},{y2}\" fill=\"none\" stroke=\"#AEB0C0\" stroke-opacity=\"0.34\" stroke-width=\"5\" stroke-linecap=\"round\"/>
<path d=\"M{x1},{y1} Q{cx},{cy} {x2},{y2}\" fill=\"none\" stroke=\"{flow}\" stroke-width=\"10\" stroke-linecap=\"round\" opacity=\"0.88\"/>
{label_svg}"""


def _particle_svg(index: int) -> str:
    x = 62 + (index * 137) % 770
    y = 148 + (index * 83) % 410
    color = ["#FF2E6F", "#39E508", "#FFD400"][index % 3]
    return f"<circle cx=\"{x}\" cy=\"{y}\" r=\"{3 + index % 4}\" fill=\"{color}\" opacity=\"0.6\"/>"


def _kind_from_text(text: str) -> str:
    low = text.lower()
    if any(k in low for k in ("data", "server", "center", "compute", "cloud")):
        return "server_rack"
    if any(k in low for k in ("power", "energy", "electric", "grid")):
        return "power_tower"
    if any(k in low for k in ("chip", "ai", "semiconductor", "gpu")):
        return "chip"
    if any(k in low for k in ("country", "nation", "city", "building", "econom")):
        return "building"
    if any(k in low for k in ("global", "traffic", "network", "internet")):
        return "globe_network"
    return "node"


def _safe_slug(value: str) -> str:
    slug = "".join(ch.lower() if ch.isalnum() else "-" for ch in value).strip("-")
    return slug or "scene"
