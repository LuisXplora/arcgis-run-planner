"""Symmetric-mode planner.

The control string is treated as the centreline of an approximately
symmetric polygon. We compute, per sample station, the perpendicular
distance to the polygon boundary on each side, choose a run count N
that respects width constraints, and emit N runs per side whose widths
vary linearly between stations to follow taper.
"""

from __future__ import annotations

from shapely.geometry import LineString, MultiPolygon, Polygon

from engine.geometry import (
    build_run_strip,
    distance_to_boundary,
    offset_centerline,
    sample_stations,
)
from engine.models import (
    Constraints,
    ControlString,
    Diagnostic,
    Mode,
    Run,
    RunPlan,
    Severity,
    Side,
    WorkArea,
)
from engine.solver import choose_run_count_symmetric


# Tolerance for "centreline is inside polygon" check (metres).
_INSIDE_TOL = 1e-3
# Tolerance for "polygon is symmetric" check (relative).
_SYMMETRY_TOL = 0.05


def plan(
    work_area: WorkArea,
    control: ControlString,
    constraints: Constraints,
) -> RunPlan:
    """Compute a symmetric-mode run plan."""
    diagnostics: list[Diagnostic] = []

    stations = sample_stations(control.line, constraints.station_step_m)

    d_left = [
        distance_to_boundary(control.line, s, work_area.polygon, Side.LEFT) for s in stations
    ]
    d_right = [
        distance_to_boundary(control.line, s, work_area.polygon, Side.RIGHT) for s in stations
    ]

    # ----- validate centreline placement ------------------------------------
    if any(d <= _INSIDE_TOL for d in d_left + d_right):
        diagnostics.append(Diagnostic(
            severity=Severity.ERROR,
            code="CENTRELINE_OUT_OF_POLYGON",
            message=(
                "At one or more stations the perpendicular distance to the polygon "
                "boundary is ~0 on at least one side; the control string may not lie "
                "fully inside the work area, or the polygon is degenerate."
            ),
            payload={
                "stations": stations,
                "d_left": d_left,
                "d_right": d_right,
            },
        ))
        return RunPlan(
            work_area=work_area,
            control=control,
            constraints=constraints,
            mode=Mode.SYMMETRIC,
            runs=[],
            diagnostics=diagnostics,
        )

    # ----- symmetry check ---------------------------------------------------
    asym = max(
        abs(dl - dr) / max(dl, dr) for dl, dr in zip(d_left, d_right)
    )
    if asym > _SYMMETRY_TOL:
        diagnostics.append(Diagnostic(
            severity=Severity.WARNING,
            code="ASYMMETRY_DETECTED",
            message=(
                f"Polygon is up to {100 * asym:.1f}% asymmetric about the control "
                f"string at some station (tolerance {100 * _SYMMETRY_TOL:.0f}%). "
                f"Consider asymmetric mode for a more accurate fit."
            ),
            payload={"max_asymmetry": asym},
        ))

    # ----- choose run count -------------------------------------------------
    n, n_diags = choose_run_count_symmetric(d_left, d_right, constraints)
    diagnostics.extend(n_diags)

    # ----- build runs -------------------------------------------------------
    runs: list[Run] = []
    for side, distances in ((Side.LEFT, d_left), (Side.RIGHT, d_right)):
        for k in range(n):
            inner_offsets = [d * k / n for d in distances]
            outer_offsets = [d * (k + 1) / n for d in distances]

            run_poly = build_run_strip(
                control.line, stations, inner_offsets, outer_offsets, side
            )
            clipped = _clip_to_polygon(run_poly, work_area.polygon)
            if clipped is None:
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    code="DEGENERATE_RUN",
                    message=f"Run {side.value}#{k} is empty after clipping; skipped.",
                ))
                continue

            mid_offsets = [d * (k + 0.5) / n for d in distances]
            run_centerline = offset_centerline(
                control.line, stations, mid_offsets, side
            )

            w_start = outer_offsets[0] - inner_offsets[0]
            w_end = outer_offsets[-1] - inner_offsets[-1]

            # Constraint-violation flagging (per run, post-build).
            if w_start < constraints.w_min - 1e-6 or w_end < constraints.w_min - 1e-6:
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    code="RUN_BELOW_MIN_WIDTH",
                    message=f"Run {side.value}#{k} width "
                            f"{w_start:.2f}->{w_end:.2f} m falls below w_min={constraints.w_min}.",
                ))
            if w_start > constraints.w_max + 1e-6 or w_end > constraints.w_max + 1e-6:
                diagnostics.append(Diagnostic(
                    severity=Severity.WARNING,
                    code="RUN_ABOVE_MAX_WIDTH",
                    message=f"Run {side.value}#{k} width "
                            f"{w_start:.2f}->{w_end:.2f} m exceeds w_max={constraints.w_max}.",
                ))

            runs.append(Run(
                side=side,
                ordinal=k,
                polygon=clipped,
                centerline=run_centerline,
                w_start=float(w_start),
                w_end=float(w_end),
                length_m=float(run_centerline.length),
                area_m2=float(clipped.area),
            ))

    return RunPlan(
        work_area=work_area,
        control=control,
        constraints=constraints,
        mode=Mode.SYMMETRIC,
        runs=runs,
        diagnostics=diagnostics,
    )


def _clip_to_polygon(geom, polygon: Polygon) -> Polygon | None:
    """Clip a strip polygon to the work area, returning a single Polygon or None."""
    clipped = geom.intersection(polygon)
    if clipped.is_empty:
        return None
    if isinstance(clipped, Polygon):
        return clipped
    if isinstance(clipped, MultiPolygon):
        # Pick the largest piece. For well-formed inputs there should only be one;
        # MultiPolygon is a sign of either a self-intersection or a concave area.
        return max(clipped.geoms, key=lambda g: g.area)
    if isinstance(clipped, LineString):
        return None
    # GeometryCollection or other — extract polygon parts.
    polys = [g for g in getattr(clipped, "geoms", []) if isinstance(g, Polygon)]
    if not polys:
        return None
    return max(polys, key=lambda g: g.area)
