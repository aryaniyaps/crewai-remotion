from __future__ import annotations

import json
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


class TraceRecorder:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.path = output_dir / "traces" / "trace.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._spans: list[dict] = []

    @contextmanager
    def span(self, phase: str) -> Iterator[None]:
        start = time.time()
        try:
            yield
            status = "ok"
        except Exception as exc:
            status = "error"
            self._spans.append({"phase": phase, "status": status, "duration_ms": int((time.time() - start) * 1000), "error": str(exc)})
            raise
        self._spans.append({"phase": phase, "status": status, "duration_ms": int((time.time() - start) * 1000)})

    def flush(self) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            for span in self._spans:
                f.write(json.dumps(span) + "\n")
        self._spans.clear()
