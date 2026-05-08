"""Edge-referenced mode planner — STUB.

In edge-referenced mode the control string is one boundary of the work area
(e.g., the runway edge for shoulder paving). Runs are offset to a single
side until the opposite boundary is reached.

Phase 1b implementation.
"""

from __future__ import annotations

from engine.models import Constraints, ControlString, RunPlan, WorkArea


def plan(
    work_area: WorkArea,  # noqa: ARG001
    control: ControlString,  # noqa: ARG001
    constraints: Constraints,  # noqa: ARG001
) -> RunPlan:
    raise NotImplementedError(
        "Edge-referenced mode is not implemented yet (Phase 1b)."
    )
