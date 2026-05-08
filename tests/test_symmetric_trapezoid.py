"""End-to-end test: symmetric mode on the trapezoid case (taper).

Hand-computed expectation: trapezoid widening from 14 m at x=0 to 18 m at
x=100, centred on y=8. With default constraints, N=2 per side. Each run
should taper from 3.5 m at x=0 to 4.5 m at x=100.

Phase 1a target accuracy: tapered widths within 50 mm of the analytic value
(see Phase 1 success criterion in the architecture document).
"""

from __future__ import annotations

import pytest

from engine import Mode, Severity, compute_runs
from engine.models import Side

WIDTH_TOL_M = 0.05  # 50 mm — Phase 1 target


def test_trapezoid_produces_four_runs(trapezoid_case, default_constraints):
    work_area, control = trapezoid_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.SYMMETRIC)

    errors = [d for d in plan.diagnostics if d.severity == Severity.ERROR]
    assert errors == [], f"Unexpected errors: {errors}"
    assert len(plan.runs) == 4, plan.summary()


def test_trapezoid_run_widths_taper(trapezoid_case, default_constraints):
    work_area, control = trapezoid_case
    plan = compute_runs(work_area, control, default_constraints)

    for run in plan.runs:
        assert run.w_start == pytest.approx(3.5, abs=WIDTH_TOL_M), run
        assert run.w_end == pytest.approx(4.5, abs=WIDTH_TOL_M), run
        assert run.w_end > run.w_start


def test_trapezoid_full_coverage(trapezoid_case, default_constraints):
    work_area, control = trapezoid_case
    plan = compute_runs(work_area, control, default_constraints)

    # Polygon area = (14 + 18) / 2 * 100 = 1600 m^2.
    assert work_area.area_m2 == pytest.approx(1600.0, rel=1e-3)
    assert plan.total_area_m2 == pytest.approx(work_area.area_m2, rel=0.01)


def test_trapezoid_balanced_left_right(trapezoid_case, default_constraints):
    work_area, control = trapezoid_case
    plan = compute_runs(work_area, control, default_constraints)

    left_runs = [r for r in plan.runs if r.side == Side.LEFT]
    right_runs = [r for r in plan.runs if r.side == Side.RIGHT]
    assert len(left_runs) == len(right_runs) == 2

    # Both sides should taper identically because polygon is symmetric.
    for l, r in zip(sorted(left_runs, key=lambda x: x.ordinal),
                    sorted(right_runs, key=lambda x: x.ordinal)):
        assert l.w_start == pytest.approx(r.w_start, abs=1e-3)
        assert l.w_end == pytest.approx(r.w_end, abs=1e-3)


def test_trapezoid_no_asymmetry_warning(trapezoid_case, default_constraints):
    """Polygon IS symmetric about the centreline; we should not emit
    ASYMMETRY_DETECTED."""
    work_area, control = trapezoid_case
    plan = compute_runs(work_area, control, default_constraints)
    codes = [d.code for d in plan.diagnostics]
    assert "ASYMMETRY_DETECTED" not in codes, plan.summary()
