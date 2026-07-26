"""End-to-end tests: edge-referenced mode on the runway_shoulder fixture.

Hand-computed expectations:
  - Work area: 150 m x 10.5 m strip (area = 1575 m^2).
  - Control string on the bottom edge (y=0); work side is LEFT.
  - With default constraints (w_min=2.7, w_max=4.5, w_pref=3.5):
      N=3 runs, each 3.5 m wide.
  - Total: 3 runs, 100% coverage, all on the LEFT side.
"""

from __future__ import annotations

import pytest

from engine import Mode, Severity, compute_runs
from engine.models import Side

WIDTH_TOL_M = 0.05  # 50 mm — Phase 1 target


def test_shoulder_produces_three_runs(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)

    errors = [d for d in plan.diagnostics if d.severity == Severity.ERROR]
    assert errors == [], f"Unexpected errors: {errors}"
    assert len(plan.runs) == 3, plan.summary()


def test_shoulder_all_runs_on_one_side(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)

    sides = {r.side for r in plan.runs}
    assert len(sides) == 1, f"Expected runs on a single side, got sides: {sides}"
    assert Side.LEFT in sides


def test_shoulder_widths_near_preferred(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)

    for run in plan.runs:
        assert run.w_start == pytest.approx(3.5, abs=WIDTH_TOL_M), run
        assert run.w_end == pytest.approx(3.5, abs=WIDTH_TOL_M), run


def test_shoulder_widths_within_constraints(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)

    for run in plan.runs:
        assert run.w_start >= default_constraints.w_min - WIDTH_TOL_M, run
        assert run.w_start <= default_constraints.w_max + WIDTH_TOL_M, run
        assert run.w_end >= default_constraints.w_min - WIDTH_TOL_M, run
        assert run.w_end <= default_constraints.w_max + WIDTH_TOL_M, run


def test_shoulder_full_coverage(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)

    assert work_area.area_m2 == pytest.approx(1575.0, rel=1e-3)
    assert plan.total_area_m2 == pytest.approx(work_area.area_m2, rel=0.01)
    assert plan.coverage_ratio == pytest.approx(1.0, abs=0.01)


def test_shoulder_runs_within_polygon(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)

    for run in plan.runs:
        outside = run.polygon.difference(work_area.polygon).area
        assert outside < 1e-3, (
            f"Run {run.side.value}#{run.ordinal} extends {outside:.6f} m^2 outside work area"
        )


def test_shoulder_run_lengths(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)

    for run in plan.runs:
        assert run.length_m == pytest.approx(150.0, abs=0.5), run


def test_shoulder_ordinals_sequential(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)

    ordinals = sorted(r.ordinal for r in plan.runs)
    assert ordinals == list(range(len(plan.runs)))


def test_shoulder_mode_is_edge_referenced(runway_shoulder_case, default_constraints):
    work_area, control = runway_shoulder_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.EDGE_REFERENCED)
    assert plan.mode == Mode.EDGE_REFERENCED
