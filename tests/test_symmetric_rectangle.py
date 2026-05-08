"""End-to-end test: symmetric mode on the rectangle case.

Hand-computed expectation: a 100 m x 14 m rectangle with centreline y=7
and default constraints (w_min=2.7, w_max=4.5, w_pref=3.5) should produce
exactly 4 runs (2 per side), each 3.5 m wide and 100 m long.
"""

from __future__ import annotations

import pytest

from engine import Mode, Severity, compute_runs
from engine.models import Side


def test_rectangle_produces_four_runs(rectangle_case, default_constraints):
    work_area, control = rectangle_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.SYMMETRIC)

    # No errors expected.
    errors = [d for d in plan.diagnostics if d.severity == Severity.ERROR]
    assert errors == [], f"Unexpected errors: {errors}"

    # 2 runs per side = 4 total.
    assert len(plan.runs) == 4, plan.summary()


def test_rectangle_run_widths_are_constant(rectangle_case, default_constraints):
    work_area, control = rectangle_case
    plan = compute_runs(work_area, control, default_constraints)

    for run in plan.runs:
        assert run.w_start == pytest.approx(3.5, abs=1e-3), run
        assert run.w_end == pytest.approx(3.5, abs=1e-3), run


def test_rectangle_run_lengths_match_polygon(rectangle_case, default_constraints):
    work_area, control = rectangle_case
    plan = compute_runs(work_area, control, default_constraints)

    for run in plan.runs:
        assert run.length_m == pytest.approx(100.0, abs=0.5), run


def test_rectangle_full_coverage(rectangle_case, default_constraints):
    work_area, control = rectangle_case
    plan = compute_runs(work_area, control, default_constraints)

    # Total run area should match the work-area area within rounding.
    assert plan.total_area_m2 == pytest.approx(work_area.area_m2, rel=0.005)
    assert plan.coverage_ratio == pytest.approx(1.0, abs=0.005)


def test_rectangle_runs_balanced_left_right(rectangle_case, default_constraints):
    work_area, control = rectangle_case
    plan = compute_runs(work_area, control, default_constraints)

    left_runs = [r for r in plan.runs if r.side == Side.LEFT]
    right_runs = [r for r in plan.runs if r.side == Side.RIGHT]
    assert len(left_runs) == len(right_runs) == 2


def test_rectangle_runs_within_polygon(rectangle_case, default_constraints):
    work_area, control = rectangle_case
    plan = compute_runs(work_area, control, default_constraints)

    for run in plan.runs:
        # Allow tiny numeric overhang from boolean ops.
        outside = run.polygon.difference(work_area.polygon).area
        assert outside < 1e-3, f"Run {run.side.value}#{run.ordinal} extends "\
                               f"{outside:.6f} m^2 outside the work area"
