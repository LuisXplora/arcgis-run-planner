"""Asymmetric-mode planner.

The control string is a reference but the polygon is NOT symmetric about it.
Each side gets its own run count chosen independently against the width
constraints, then run polygons are built with the same geometry helpers used
by symmetric mode.
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
from engine.solver import choose_run_count_per_side


_INSIDE_TOL = 1e-3


def plan(
    work_area: WorkArea,
    control: ControlString,
    constraints: Constraints,
) -> RunPlan:
    """Compute an asymmetric-mode run plan."""
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
            payload={"stations": stations, "d_left": d_left, "d_right": d_right},
        ))
        return RunPlan(
            work_area=work_area,
            control=control,
            constraints=constraints,
            mode=Mode.ASYMMETRIC,
            runs=[],
            diagnostics=diagnostics,
        )

    # ----- choose run count independently per side -------------------------
    n_left, left_diags = choose_run_count_per_side(d_left, constraints, side_label="left")
    n_right, right_diags = choose_run_count_per_side(d_right, constraints, side_label="right")
    diagnostics.extend(left_diags)
    diagnostics.extend(right_diags)

    # ----- build runs -------------------------------------------------------
    runs: list[Run] = []
    for side, distances, n in (
        (Side.LEFT, d_left, n_left),
        (Side.RIGHT, d_right, n_right),
    ):
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
            run_centerline = offset_centerline(control.line, stations, mid_offsets, side)

            w_start = outer_offsets[0] - inner_offsets[0]
            w_end = outer_offsets[-1] - inner_offsets[-1]

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
        mode=Mode.ASYMMETRIC,
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
        return max(clipped.geoms, key=lambda g: g.area)
    if isinstance(clipped, LineString):
        return None
    polys = [g for g in getattr(clipped, "geoms", []) if isinstance(g, Polygon)]
    if not polys:
        return None
    return max(polys, key=lambda g: g.area)
