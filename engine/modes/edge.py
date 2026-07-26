"""Edge-referenced mode planner.

The control string lies on one boundary of the work area (e.g., a runway
pavement edge for shoulder paving). All runs offset to a single side,
stepping outward from the control string to the opposite boundary.
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


# Minimum distance (m) for a side to be considered the work side.
_WORK_SIDE_TOL = 0.5


def plan(
    work_area: WorkArea,
    control: ControlString,
    constraints: Constraints,
) -> RunPlan:
    """Compute an edge-referenced run plan."""
    diagnostics: list[Diagnostic] = []

    stations = sample_stations(control.line, constraints.station_step_m)

    d_left = [
        distance_to_boundary(control.line, s, work_area.polygon, Side.LEFT) for s in stations
    ]
    d_right = [
        distance_to_boundary(control.line, s, work_area.polygon, Side.RIGHT) for s in stations
    ]

    # ----- detect work side -------------------------------------------------
    left_max = max(d_left)
    right_max = max(d_right)

    has_left = left_max >= _WORK_SIDE_TOL
    has_right = right_max >= _WORK_SIDE_TOL

    if not has_left and not has_right:
        diagnostics.append(Diagnostic(
            severity=Severity.ERROR,
            code="CENTRELINE_OUT_OF_POLYGON",
            message=(
                "No significant distance to the polygon boundary on either side. "
                "The control string may lie outside the work area."
            ),
            payload={"d_left_max": left_max, "d_right_max": right_max},
        ))
        return RunPlan(
            work_area=work_area,
            control=control,
            constraints=constraints,
            mode=Mode.EDGE_REFERENCED,
            runs=[],
            diagnostics=diagnostics,
        )

    if has_left and has_right:
        # Control string is not on a boundary — warn and pick the wider side.
        work_side = Side.LEFT if left_max >= right_max else Side.RIGHT
        diagnostics.append(Diagnostic(
            severity=Severity.WARNING,
            code="NOT_EDGE_REFERENCED",
            message=(
                f"Work area has significant width on both sides of the control string "
                f"(left max {left_max:.2f} m, right max {right_max:.2f} m). "
                f"Edge-referenced mode expects the string on a boundary. "
                f"Proceeding on the wider side ({work_side.value}). "
                f"Consider asymmetric mode for a two-sided layout."
            ),
            payload={"left_max": left_max, "right_max": right_max},
        ))
    else:
        work_side = Side.LEFT if has_left else Side.RIGHT

    distances = d_left if work_side == Side.LEFT else d_right

    # ----- choose run count -------------------------------------------------
    n, n_diags = choose_run_count_per_side(distances, constraints, side_label=work_side.value)
    diagnostics.extend(n_diags)

    # ----- build runs -------------------------------------------------------
    runs: list[Run] = []
    for k in range(n):
        inner_offsets = [d * k / n for d in distances]
        outer_offsets = [d * (k + 1) / n for d in distances]

        run_poly = build_run_strip(
            control.line, stations, inner_offsets, outer_offsets, work_side
        )
        clipped = _clip_to_polygon(run_poly, work_area.polygon)
        if clipped is None:
            diagnostics.append(Diagnostic(
                severity=Severity.WARNING,
                code="DEGENERATE_RUN",
                message=f"Run {work_side.value}#{k} is empty after clipping; skipped.",
            ))
            continue

        mid_offsets = [d * (k + 0.5) / n for d in distances]
        run_centerline = offset_centerline(control.line, stations, mid_offsets, work_side)

        w_start = outer_offsets[0] - inner_offsets[0]
        w_end = outer_offsets[-1] - inner_offsets[-1]

        if w_start < constraints.w_min - 1e-6 or w_end < constraints.w_min - 1e-6:
            diagnostics.append(Diagnostic(
                severity=Severity.WARNING,
                code="RUN_BELOW_MIN_WIDTH",
                message=f"Run {work_side.value}#{k} width "
                        f"{w_start:.2f}->{w_end:.2f} m falls below w_min={constraints.w_min}.",
            ))
        if w_start > constraints.w_max + 1e-6 or w_end > constraints.w_max + 1e-6:
            diagnostics.append(Diagnostic(
                severity=Severity.WARNING,
                code="RUN_ABOVE_MAX_WIDTH",
                message=f"Run {work_side.value}#{k} width "
                        f"{w_start:.2f}->{w_end:.2f} m exceeds w_max={constraints.w_max}.",
            ))

        runs.append(Run(
            side=work_side,
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
        mode=Mode.EDGE_REFERENCED,
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
