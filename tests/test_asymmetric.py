"""End-to-end tests: asymmetric mode on the taxiway_tiein fixture.

Hand-computed expectations:
  - Work area: 100 m x 21 m rectangle (area = 2100 m^2).
  - Control string at y=7: left side 14 m, right side 7 m.
  - With default constraints (w_min=2.7, w_max=4.5, w_pref=3.5):
      left  → N=4 runs, each 3.5 m wide
      right → N=2 runs, each 3.5 m wide
  - Total: 6 runs, 100% coverage.
"""

from __future__ import annotations

import pytest

from engine import Mode, Severity, compute_runs
from engine.models import Side

WIDTH_TOL_M = 0.05  # 50 mm — Phase 1 target


def test_taxiway_produces_six_runs(taxiway_tiein_case, default_constraints):
    work_area, control = taxiway_tiein_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.ASYMMETRIC)

    errors = [d for d in plan.diagnostics if d.severity == Severity.ERROR]
    assert errors == [], f"Unexpected errors: {errors}"
    assert len(plan.runs) == 6, plan.summary()


def test_taxiway_sides_have_independent_run_counts(taxiway_tiein_case, default_constraints):
    work_area, control = taxiway_tiein_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.ASYMMETRIC)

    left_runs = [r for r in plan.runs if r.side == Side.LEFT]
    right_runs = [r for r in plan.runs if r.side == Side.RIGHT]
    assert len(left_runs) == 4, f"Expected 4 left runs, got {len(left_runs)}"
    assert len(right_runs) == 2, f"Expected 2 right runs, got {len(right_runs)}"
    assert len(left_runs) != len(right_runs), "Sides should have different run counts"


def test_taxiway_widths_within_constraints(taxiway_tiein_case, default_constraints):
    work_area, control = taxiway_tiein_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.ASYMMETRIC)

    for run in plan.runs:
        assert run.w_start >= default_constraints.w_min - WIDTH_TOL_M, run
        assert run.w_start <= default_constraints.w_max + WIDTH_TOL_M, run
        assert run.w_end >= default_constraints.w_min - WIDTH_TOL_M, run
        assert run.w_end <= default_constraints.w_max + WIDTH_TOL_M, run


def test_taxiway_widths_near_preferred(taxiway_tiein_case, default_constraints):
    work_area, control = taxiway_tiein_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.ASYMMETRIC)

    for run in plan.runs:
        assert run.w_start == pytest.approx(3.5, abs=WIDTH_TOL_M), run
        assert run.w_end == pytest.approx(3.5, abs=WIDTH_TOL_M), run


def test_taxiway_full_coverage(taxiway_tiein_case, default_constraints):
    work_area, control = taxiway_tiein_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.ASYMMETRIC)

    assert work_area.area_m2 == pytest.approx(2100.0, rel=1e-3)
    assert plan.total_area_m2 == pytest.approx(work_area.area_m2, rel=0.01)
    assert plan.coverage_ratio == pytest.approx(1.0, abs=0.01)


def test_taxiway_runs_within_polygon(taxiway_tiein_case, default_constraints):
    work_area, control = taxiway_tiein_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.ASYMMETRIC)

    for run in plan.runs:
        outside = run.polygon.difference(work_area.polygon).area
        assert outside < 1e-3, (
            f"Run {run.side.value}#{run.ordinal} extends {outside:.6f} m^2 outside work area"
        )


def test_taxiway_run_lengths(taxiway_tiein_case, default_constraints):
    work_area, control = taxiway_tiein_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.ASYMMETRIC)

    for run in plan.runs:
        assert run.length_m == pytest.approx(100.0, abs=0.5), run


def test_taxiway_mode_is_asymmetric(taxiway_tiein_case, default_constraints):
    work_area, control = taxiway_tiein_case
    plan = compute_runs(work_area, control, default_constraints, mode=Mode.ASYMMETRIC)
    assert plan.mode == Mode.ASYMMETRIC
