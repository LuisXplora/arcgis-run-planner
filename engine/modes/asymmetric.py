"""Asymmetric-mode planner — STUB.

In asymmetric mode the control string is a reference but the polygon is not
symmetric about it. Each side gets its own run count and width sequence.

Phase 1b implementation. For Phase 1a this raises NotImplementedError so
callers fail loudly rather than silently producing wrong runs.
"""

from __future__ import annotations

from engine.models import Constraints, ControlString, RunPlan, WorkArea


def plan(
    work_area: WorkArea,  # noqa: ARG001 — reserved
    control: ControlString,  # noqa: ARG001
    constraints: Constraints,  # noqa: ARG001
) -> RunPlan:
    raise NotImplementedError(
        "Asymmetric mode is not implemented yet (Phase 1b). "
        "Use Mode.SYMMETRIC for now, and the engine will emit an "
        "ASYMMETRY_DETECTED diagnostic if the polygon needs asymmetric handling."
    )
