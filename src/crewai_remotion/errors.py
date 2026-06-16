from __future__ import annotations


class ProductionError(Exception):
    """User-facing pipeline failure with recovery hints."""

    def __init__(
        self,
        message: str,
        *,
        phase: str = "",
        hint: str = "",
        run_dir: str = "",
    ) -> None:
        super().__init__(message)
        self.message = message
        self.phase = phase
        self.hint = hint
        self.run_dir = run_dir
