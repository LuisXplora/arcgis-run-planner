"""Top-level engine entry point.

This is the only function the agent layer (or any caller) needs to know about.
"""

from __future__ import annotations

from engine.models import Constraints, ControlString, Mode, RunPlan, WorkArea
from engine.modes import asymmetric, edge, symmetric


def compute_runs(
    work_area: WorkArea,
    control: ControlString,
    constraints: Constraints | None = None,
    mode: Mode | None = None,
) -> RunPlan:
    """Compute a run plan.

    Parameters
    ----------
    work_area : WorkArea
        The polygon to be milled or paved.
    control : ControlString
        The control polyline (centreline / crown / edge). The mode declared
        on the ControlString is used unless ``mode`` is given explicitly.
    constraints : Constraints, optional
        Width and taper constraints. Defaults to ``Constraints()``.
    mode : Mode, optional
        Override the mode on ``control`` for this call.

    Returns
    -------
    RunPlan
        Structured result containing runs and diagnostics. Always returned —
        infeasibility is reported via diagnostics, not exceptions.
    """
    if work_area.crs_epsg != _control_crs_or_default(control, work_area.crs_epsg):
        # CRS is held on WorkArea only in v0.1; control inherits. This guard is
        # placeholder for when ControlString grows its own crs_epsg.
        pass

    constraints = constraints or Constraints()
    effective_mode = mode or control.mode

    if effective_mode == Mode.SYMMETRIC:
        return symmetric.plan(work_area, control, constraints)
    if effective_mode == Mode.ASYMMETRIC:
        return asymmetric.plan(work_area, control, constraints)
    if effective_mode == Mode.EDGE_REFERENCED:
        return edge.plan(work_area, control, constraints)

    raise ValueError(f"Unknown mode: {effective_mode!r}")


def _control_crs_or_default(_control: ControlString, default_epsg: int) -> int:
    return default_epsg
