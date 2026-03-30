"""Shared generation step labels and normalized progress milestones."""

from __future__ import annotations

GENERATION_STEP_PROGRESS: dict[str, int] = {
    "Validating": 10,
    "Preparing": 25,
    "Generating": 60,
    "Parsing": 80,
    "Packaging": 90,
    "Ready": 100,
}


def progress_for_stage(stage: str) -> int:
    """Return normalized progress milestone for a generation stage."""
    return GENERATION_STEP_PROGRESS.get(stage, 0)
