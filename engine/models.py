"""Data classes for engine inputs and outputs.

All geometry is held as Shapely objects in a projected CRS with metre units.
The engine itself does not perform reprojection — see ADR 0003.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from shapely.geometry import LineString, Polygon, mapping, shape
from shapely.validation import explain_validity


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Mode(str, Enum):
    """Control-string mode. See solution architecture §5.2."""

    SYMMETRIC = "symmetric"
    ASYMMETRIC = "asymmetric"
    EDGE_REFERENCED = "edge_referenced"


class Side(str, Enum):
    """Which side of the control string a run sits on."""

    LEFT = "left"
    RIGHT = "right"


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class WorkArea:
    """The polygon to be milled or paved."""

    polygon: Polygon
    crs_epsg: int
    surface_type: str = "asphalt"
    notes: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.polygon, Polygon):
            raise TypeError("WorkArea.polygon must be a shapely.Polygon")
        if not self.polygon.is_valid:
            raise ValueError(f"WorkArea polygon is not valid: {explain_validity(self.polygon)}")
        if self.crs_epsg < 1000:  # heuristic: projected EPSG codes are 4-digit+
            raise ValueError(
                f"crs_epsg={self.crs_epsg} looks geographic. Engine requires a projected CRS "
                f"with metre units (e.g., MGA2020 zones 7850-7856). See ADR 0003."
            )

    @property
    def area_m2(self) -> float:
        return float(self.polygon.area)


@dataclass(frozen=True)
class ControlString:
    """The polyline serving as centreline / crown / edge reference."""

    line: LineString
    mode: Mode

    def __post_init__(self) -> None:
        if not isinstance(self.line, LineString):
            raise TypeError("ControlString.line must be a shapely.LineString")
        if self.line.length < 0.1:
            raise ValueError("ControlString is too short (<0.1 m).")

    @property
    def length_m(self) -> float:
        return float(self.line.length)


@dataclass(frozen=True)
class Constraints:
    """Run-width and taper constraints.

    Attributes
    ----------
    w_min : minimum allowable run width (metres).
    w_max : maximum allowable run width (metres).
    w_pref : preferred width — solver tries to land closest to this.
    taper_max : max allowable change in run width per linear metre of run.
                e.g., 0.05 = 5 cm width change per metre of length.
    runs_locked : if set, force this many runs per side. Otherwise solver picks.
    station_step_m : distance between sample stations along the control line.
    """

    w_min: float = 2.7
    w_max: float = 4.5
    w_pref: float = 3.5
    taper_max: float = 0.10
    runs_locked: int | None = None
    station_step_m: float = 5.0

    def __post_init__(self) -> None:
        if not (0 < self.w_min <= self.w_pref <= self.w_max):
            raise ValueError(
                f"Constraints must satisfy 0 < w_min ({self.w_min}) <= w_pref ({self.w_pref}) "
                f"<= w_max ({self.w_max})."
            )
        if self.taper_max < 0:
            raise ValueError("taper_max must be >= 0.")
        if self.station_step_m <= 0:
            raise ValueError("station_step_m must be > 0.")
        if self.runs_locked is not None and self.runs_locked < 1:
            raise ValueError("runs_locked must be >= 1 if provided.")


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Run:
    """A single milling/paving run."""

    side: Side
    ordinal: int                  # 0 = nearest control string, increasing outward
    polygon: Polygon              # the run footprint, clipped to the work area
    centerline: LineString        # the run's own centerline polyline
    w_start: float                # width at start of control string (metres)
    w_end: float                  # width at end of control string (metres)
    length_m: float               # length along centerline
    area_m2: float                # planar area of polygon

    @property
    def w_avg(self) -> float:
        return 0.5 * (self.w_start + self.w_end)


@dataclass(frozen=True)
class Diagnostic:
    """Engine diagnostic — warnings, infeasibilities, and notes."""

    severity: Severity
    code: str
    message: str
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunPlan:
    """The structured result of a planning call."""

    work_area: WorkArea
    control: ControlString
    constraints: Constraints
    mode: Mode
    runs: list[Run]
    diagnostics: list[Diagnostic]

    @property
    def total_area_m2(self) -> float:
        return sum(r.area_m2 for r in self.runs)

    @property
    def coverage_ratio(self) -> float:
        """Fraction of the work area covered by runs (0..1)."""
        wa = self.work_area.area_m2
        return self.total_area_m2 / wa if wa > 0 else 0.0

    def summary(self) -> str:
        lines = [
            f"RunPlan ({self.mode.value})",
            f"  work_area: {self.work_area.area_m2:.1f} m^2",
            f"  control: {self.control.length_m:.1f} m",
            f"  runs: {len(self.runs)}",
            f"  total run area: {self.total_area_m2:.1f} m^2",
            f"  coverage: {100 * self.coverage_ratio:.1f}%",
        ]
        for r in self.runs:
            lines.append(
                f"    [{r.side.value}#{r.ordinal}] "
                f"w {r.w_start:.2f}->{r.w_end:.2f} m, "
                f"len {r.length_m:.1f} m, area {r.area_m2:.1f} m^2"
            )
        if self.diagnostics:
            lines.append("  diagnostics:")
            for d in self.diagnostics:
                lines.append(f"    [{d.severity.value}] {d.code}: {d.message}")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# GeoJSON loaders (test-fixture convenience)
# ---------------------------------------------------------------------------

def load_geojson_case(
    path: str | Path,
    mode: Mode = Mode.SYMMETRIC,
) -> tuple[WorkArea, ControlString]:
    """Load a GeoJSON FeatureCollection containing a 'work_area' polygon and
    a 'control_string' polyline (identified by feature.properties.role).

    Used by tests and examples; not part of the production API.
    """
    path = Path(path)
    with path.open() as f:
        data = json.load(f)

    crs_name = data.get("crs", {}).get("properties", {}).get("name", "")
    crs_epsg = _parse_epsg(crs_name)

    work_area_geom: Polygon | None = None
    control_geom: LineString | None = None

    for feat in data.get("features", []):
        role = feat.get("properties", {}).get("role")
        geom = shape(feat["geometry"])
        if role == "work_area" and isinstance(geom, Polygon):
            work_area_geom = geom
        elif role == "control_string" and isinstance(geom, LineString):
            control_geom = geom

    if work_area_geom is None:
        raise ValueError(f"No 'work_area' polygon in {path}")
    if control_geom is None:
        raise ValueError(f"No 'control_string' polyline in {path}")

    return (
        WorkArea(polygon=work_area_geom, crs_epsg=crs_epsg),
        ControlString(line=control_geom, mode=mode),
    )


def _parse_epsg(crs_name: str) -> int:
    """Parse 'urn:ogc:def:crs:EPSG::7856' -> 7856."""
    if "EPSG" not in crs_name:
        return 7856  # fallback for fixtures without explicit CRS
    tail = crs_name.rsplit(":", 1)[-1]
    try:
        return int(tail)
    except ValueError:
        return 7856


def runs_to_geojson(plan: RunPlan) -> dict[str, Any]:
    """Convert a RunPlan to a GeoJSON FeatureCollection (one feature per run)."""
    features = []
    for r in plan.runs:
        features.append({
            "type": "Feature",
            "properties": {
                "side": r.side.value,
                "ordinal": r.ordinal,
                "w_start": round(r.w_start, 4),
                "w_end": round(r.w_end, 4),
                "length_m": round(r.length_m, 3),
                "area_m2": round(r.area_m2, 3),
            },
            "geometry": mapping(r.polygon),
        })
    return {
        "type": "FeatureCollection",
        "name": "run_plan",
        "crs": {
            "type": "name",
            "properties": {"name": f"urn:ogc:def:crs:EPSG::{plan.work_area.crs_epsg}"},
        },
        "features": features,
    }
