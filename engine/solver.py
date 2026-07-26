"""Run-count and width selection.

Deliberately kept simple for Phase 1a: an integer search over N (number of
runs per side) that minimises sum-of-squared-deviations from preferred width
across all sample stations, subject to per-station width staying within
[w_min, w_max]. Phase 1b can swap this out for an LP/QP solver if needed.
"""

from __future__ import annotations

import math

from engine.models import Constraints, Diagnostic, Severity


def _ceil_safe(x: float) -> int:
    """Ceiling with a tiny epsilon to avoid floating-point off-by-one."""
    return int(math.ceil(x - 1e-9))


def _floor_safe(x: float) -> int:
    return int(math.floor(x + 1e-9))


def choose_run_count_symmetric(
    d_left: list[float],
    d_right: list[float],
    constraints: Constraints,
) -> tuple[int, list[Diagnostic]]:
    """Pick N (runs per side) for symmetric mode.

    Returns (N, diagnostics). N >= 1 always — even when constraints are
    infeasible we return our best-effort N and emit a warning rather than
    raising.
    """
    diagnostics: list[Diagnostic] = []

    # User override wins.
    if constraints.runs_locked is not None:
        return constraints.runs_locked, diagnostics

    if not d_left or not d_right:
        return 1, [Diagnostic(Severity.ERROR, "NO_STATIONS",
                              "No sample stations available to choose run count.")]

    # Bounds: N must be high enough that w = d/N <= w_max for the worst (max d)
    # station, and low enough that w >= w_min for the best (min d) station.
    d_max = max(max(d_left), max(d_right))
    d_min = min(min(d_left), min(d_right))

    n_lo = max(1, _ceil_safe(d_max / constraints.w_max))
    n_hi = max(1, _floor_safe(d_min / constraints.w_min))

    feasible = n_lo <= n_hi
    if not feasible:
        # Pick N that puts AVERAGE width nearest w_pref, accept the violation.
        d_avg = 0.5 * (d_max + d_min)
        n_pref = max(1, round(d_avg / constraints.w_pref))
        diagnostics.append(Diagnostic(
            severity=Severity.WARNING,
            code="INFEASIBLE_WIDTH_BOUNDS",
            message=(
                f"No run count satisfies w in [{constraints.w_min}, {constraints.w_max}] "
                f"across all stations (d ranges {d_min:.2f}..{d_max:.2f} m per side). "
                f"Falling back to N={n_pref}; some runs will violate bounds."
            ),
            payload={"n_lo": n_lo, "n_hi": n_hi, "d_max": d_max, "d_min": d_min},
        ))
        return n_pref, diagnostics

    # Search the feasible range and pick the N minimising width variance from w_pref.
    best_n = n_lo
    best_score = float("inf")
    all_d = d_left + d_right
    for n in range(n_lo, n_hi + 1):
        widths = [d / n for d in all_d]
        score = sum((w - constraints.w_pref) ** 2 for w in widths)
        if score < best_score:
            best_score = score
            best_n = n

    # Annotate when picked N forces tight widths.
    widths_at_n = [d / best_n for d in all_d]
    if max(widths_at_n) - min(widths_at_n) > constraints.w_max - constraints.w_min:
        diagnostics.append(Diagnostic(
            severity=Severity.INFO,
            code="WIDE_TAPER",
            message=(
                f"Selected N={best_n}; per-station width ranges "
                f"{min(widths_at_n):.2f}..{max(widths_at_n):.2f} m."
            ),
        ))

    return best_n, diagnostics


def choose_run_count_per_side(
    d: list[float],
    constraints: Constraints,
    side_label: str = "",
) -> tuple[int, list[Diagnostic]]:
    """Pick N (run count) for a single side in asymmetric mode.

    Same selection logic as choose_run_count_symmetric but operates on one
    side's distance list independently. Returns (N, diagnostics); N >= 1 always.
    """
    diagnostics: list[Diagnostic] = []

    if constraints.runs_locked is not None:
        return constraints.runs_locked, diagnostics

    if not d:
        return 1, [Diagnostic(Severity.ERROR, "NO_STATIONS",
                              f"No sample stations available ({side_label}).")]

    d_max = max(d)
    d_min = min(d)

    n_lo = max(1, _ceil_safe(d_max / constraints.w_max))
    n_hi = max(1, _floor_safe(d_min / constraints.w_min))

    label = f" ({side_label})" if side_label else ""

    feasible = n_lo <= n_hi
    if not feasible:
        d_avg = 0.5 * (d_max + d_min)
        n_pref = max(1, round(d_avg / constraints.w_pref))
        diagnostics.append(Diagnostic(
            severity=Severity.WARNING,
            code="INFEASIBLE_WIDTH_BOUNDS",
            message=(
                f"No run count satisfies w in [{constraints.w_min}, {constraints.w_max}] "
                f"across all stations{label} (d ranges {d_min:.2f}..{d_max:.2f} m). "
                f"Falling back to N={n_pref}; some runs will violate bounds."
            ),
            payload={"n_lo": n_lo, "n_hi": n_hi, "d_max": d_max, "d_min": d_min},
        ))
        return n_pref, diagnostics

    best_n = n_lo
    best_score = float("inf")
    for n in range(n_lo, n_hi + 1):
        widths = [d_i / n for d_i in d]
        score = sum((w - constraints.w_pref) ** 2 for w in widths)
        if score < best_score:
            best_score = score
            best_n = n

    widths_at_n = [d_i / best_n for d_i in d]
    if max(widths_at_n) - min(widths_at_n) > constraints.w_max - constraints.w_min:
        diagnostics.append(Diagnostic(
            severity=Severity.INFO,
            code="WIDE_TAPER",
            message=(
                f"Selected N={best_n}{label}; per-station width ranges "
                f"{min(widths_at_n):.2f}..{max(widths_at_n):.2f} m."
            ),
        ))

    return best_n, diagnostics
