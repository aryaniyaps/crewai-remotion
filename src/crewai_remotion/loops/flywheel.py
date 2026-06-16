from __future__ import annotations

import json
from pathlib import Path

import yaml

from crewai_remotion.config import get_settings
from crewai_remotion.models.production_state import ProductionState


def _learnings_path() -> Path:
    settings = get_settings()
    return settings.root / "src" / "crewai_remotion" / "loops" / "learnings" / "global.yaml"


def _load_learnings() -> list[dict]:
    path = _learnings_path()
    if not path.exists():
        return []
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data.get("lessons", [])


def _save_learnings(lessons: list[dict]) -> None:
    path = _learnings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.dump({"lessons": lessons}, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def recall_lessons(state: ProductionState) -> None:
    """Load global learnings and inject relevant lessons into flywheel_context."""
    lessons = _load_learnings()
    if not lessons:
        return

    # Inject each lesson as a context string agents can consume
    for lesson in lessons:
        dept = lesson.get("department", "general")
        mode = lesson.get("failure_mode", "unknown")
        fix = lesson.get("fix_heuristic", "")
        state.flywheel_context.append(f"[flywheel:{dept}] {mode}: {fix}")

    # Also write a recall manifest for trace
    out = state.run_output()
    out.mkdir(parents=True, exist_ok=True)
    (out / "flywheel_recall.json").write_text(
        json.dumps({"recalled": len(lessons), "source": str(_learnings_path())}),
        encoding="utf-8",
    )


def distill_from_trace(trace_path: Path) -> dict:
    """Extract lessons from trace and production notes."""
    if not trace_path.exists():
        return {"lessons": []}

    lines = trace_path.read_text(encoding="utf-8").strip().splitlines()
    slow = [json.loads(l) for l in lines if json.loads(l).get("duration_ms", 0) > 5000]
    results = {"lessons": [f"Phase {s['phase']} was slow ({s['duration_ms']}ms)" for s in slow]}

    # Also read production_notes.jsonl from the parent directory
    notes_path = trace_path.parent / "production_notes.jsonl"
    if notes_path.exists():
        note_lines = notes_path.read_text(encoding="utf-8").strip().splitlines()
        failed = [
            json.loads(l)
            for l in note_lines
            if l.strip() and not json.loads(l).get("handoff_ok", True)
        ]
        results["eval_failures"] = [
            {"phase": n["phase"], "message": n["message"]} for n in failed
        ]

    return results


def save_lessons_from_state(state: ProductionState) -> None:
    """Persist lessons from eval and gate failures to the learnings YAML.

    Called at the end of a successful run so future runs benefit from
    failures encountered during this production pipeline.
    """
    # Collect failures from production_notes.jsonl
    notes_path = state.run_output() / "production_notes.jsonl"
    raw_failures: list[dict] = []
    if notes_path.exists():
        for line in notes_path.read_text(encoding="utf-8").strip().splitlines():
            if not line.strip():
                continue
            note = json.loads(line)
            if not note.get("handoff_ok", True):
                raw_failures.append(note)

    # Collect failures from component_evals
    eval_failures: list[dict] = []
    for eval_id, result in state.component_evals.items():
        if not result.passed:
            department = getattr(result, "department", "general") or "general"
            eval_failures.append({
                "phase": department,
                "message": result.message,
                "metric_id": result.metric_id or eval_id,
            })

    # Distill into lesson format
    existing = _load_learnings()
    seen_modes = {l.get("failure_mode") for l in existing}

    for failure in raw_failures:
        msg = failure.get("message", "")
        phase = failure.get("phase", "general")

        if "Eval warnings:" in msg:
            # Extract the list representation from the message
            # Format: "Eval warnings: ['msg1', 'msg2']"
            warnings_str = msg.split("Eval warnings:", 1)[1].strip()
            try:
                import ast
                warnings = ast.literal_eval(warnings_str)
            except Exception:
                warnings = [warnings_str]
            for warning in warnings:
                mode = _failure_mode_from_message(warning)
                if mode and mode not in seen_modes:
                    seen_modes.add(mode)
                    existing.append({
                        "failure_mode": mode,
                        "fix_heuristic": warning,
                        "department": phase,
                        "evidence_run_ids": [state.run_id],
                    })
        else:
            mode = _failure_mode_from_message(msg)
            if mode and mode not in seen_modes:
                seen_modes.add(mode)
                existing.append({
                    "failure_mode": mode,
                    "fix_heuristic": msg,
                    "department": phase,
                    "evidence_run_ids": [state.run_id],
                })

    for failure in eval_failures:
        metric = failure.get("metric_id", "")
        if metric and metric not in seen_modes:
            seen_modes.add(metric)
            existing.append({
                "failure_mode": metric,
                "fix_heuristic": failure.get("message", ""),
                "department": failure.get("phase", "general"),
                "evidence_run_ids": [state.run_id],
            })

    if existing:
        _save_learnings(existing)


def _failure_mode_from_message(message: str) -> str:
    """Derive a stable failure_mode key from an eval message."""
    # Map common eval messages to stable keys
    key_map = {
        "Missing:": "brief_incomplete",
        "No creative brief": "brief_missing",
        "No AV script": "script_missing",
        "beat_count": "beat_count",
        "beat_rhythm": "beat_rhythm",
        "hook_duration": "hook_duration",
        "hook_on_screen_text": "hook_on_screen_text",
        "word_cap_per_beat": "word_cap_per_beat",
        "word_economy": "word_economy",
        "vo_line_length": "vo_line_length",
        "cta_presence": "cta_missing",
        "hook_candidates_viable": "hook_candidates_weak",
        "complexity_budget_range": "complexity_budget_out_of_range",
        "brief_completeness": "brief_incomplete",
    }
    for prefix, key in key_map.items():
        if prefix in message:
            return key
    # Fallback: use first 50 chars, sanitized
    sanitized = message.strip().lower().replace(" ", "_")[:60]
    return sanitized or "unknown_failure"
