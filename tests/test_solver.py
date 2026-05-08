"""Unit tests for the run-count solver."""

from __future__ import annotations

from engine.models import Constraints
from engine.solver import choose_run_count_symmetric


def test_chooses_n_for_constant_distance():
    # 7 m each side; w_pref=3.5 -> N=2 is exact.
    c = Constraints(w_min=2.7, w_max=4.5, w_pref=3.5)
    n, diags = choose_run_count_symmetric([7.0] * 5, [7.0] * 5, c)
    assert n == 2
    assert all(d.severity.value != "warning" for d in diags) or diags == []


def test_chooses_n_for_taper():
    # 7 m at start, 9 m at end; N=2 -> widths 3.5..4.5, both feasible.
    c = Constraints(w_min=2.7, w_max=4.5, w_pref=3.5)
    d = [7.0, 7.5, 8.0, 8.5, 9.0]
    n, _ = choose_run_count_symmetric(d, d, c)
    assert n == 2


def test_runs_locked_overrides():
    c = Constraints(runs_locked=3)
    n, diags = choose_run_count_symmetric([10.0] * 3, [10.0] * 3, c)
    assert n == 3
    assert diags == []


def test_infeasible_emits_warning():
    # Distance very large vs w_max -> N must be high; distance small vs w_min
    # at some station -> N must be low. Force conflict.
    c = Constraints(w_min=3.5, w_max=4.0, w_pref=3.7)
    d_left = [4.0, 4.0, 4.0]   # forces N=1 max (4/1 = 4)
    d_right = [12.0, 12.0, 12.0]  # forces N>=3 (12/4 = 3)
    n, diags = choose_run_count_symmetric(d_left, d_right, c)
    assert n >= 1
    assert any(d.code == "INFEASIBLE_WIDTH_BOUNDS" for d in diags)
