"""Pure-geometry helpers for the engine.

These functions know nothing about runs or constraints — they manipulate
Shapely primitives. Consumers (modes, solver) compose them.
"""

from __future__ import annotations

from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient as orient_polygon

from engine.models import Side


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def sample_stations(line: LineString, step_m: float) -> list[float]:
    """Return distances along ``line`` at ``step_m`` spacing, including 0 and L.

    A station is a 1-D coordinate along the polyline (0 at start, L at end).
    The returned list is monotonically increasing and always contains 0.0 and
    line.length, with internal stations at multiples of step_m.
    """
    L = float(line.length)
    if step_m <= 0:
        raise ValueError("step_m must be > 0")
    if L <= step_m:
        return [0.0, L]
    n = int(L // step_m)
    stations = [i * step_m for i in range(n + 1)]
    if stations[-1] < L - 1e-9:
        stations.append(L)
    return stations


def point_at_station(line: LineString, s: float) -> Point:
    """Point along ``line`` at distance ``s`` from start."""
    return line.interpolate(s)


def tangent_at_station(line: LineString, s: float, eps: float = 1e-3) -> tuple[float, float]:
    """Unit tangent vector (dx, dy) along ``line`` at station ``s``.

    Uses a small finite-difference window around s. At endpoints the window is
    shifted inward.
    """
    L = float(line.length)
    if eps <= 0:
        raise ValueError("eps must be > 0")
    if L <= 2 * eps:
        # very short line: take whole-line direction
        p0 = line.interpolate(0.0)
        p1 = line.interpolate(L)
    else:
        s0 = s - eps
        s1 = s + eps
        if s0 < 0:
            s0, s1 = 0.0, 2 * eps
        elif s1 > L:
            s0, s1 = L - 2 * eps, L
        p0 = line.interpolate(s0)
        p1 = line.interpolate(s1)
    dx, dy = p1.x - p0.x, p1.y - p0.y
    mag = (dx * dx + dy * dy) ** 0.5
    if mag < 1e-12:
        return (1.0, 0.0)
    return (dx / mag, dy / mag)


def perpendicular_unit(tangent: tuple[float, float], side: Side) -> tuple[float, float]:
    """Unit perpendicular vector to a tangent, on the given side.

    Convention: LEFT is the +90° (CCW) rotation of the tangent — matches
    shapely.parallel_offset(side='left'). RIGHT is the –90° rotation.
    """
    tx, ty = tangent
    if side == Side.LEFT:
        return (-ty, tx)
    if side == Side.RIGHT:
        return (ty, -tx)
    raise ValueError(f"Unknown side: {side!r}")


# ---------------------------------------------------------------------------
# Boundary distance (perpendicular ray casting)
# ---------------------------------------------------------------------------

def distance_to_boundary(
    line: LineString,
    s: float,
    polygon: Polygon,
    side: Side,
    max_dist: float = 1000.0,
) -> float:
    """Distance from the point on ``line`` at station ``s`` to ``polygon``'s
    boundary, along the perpendicular on the given ``side``.

    Returns 0.0 if the centreline point is on or outside the polygon on that
    side. Returns ``max_dist`` if no boundary is found within the search range.
    """
    p = point_at_station(line, s)
    t = tangent_at_station(line, s)
    perp = perpendicular_unit(t, side)
    end = (p.x + max_dist * perp[0], p.y + max_dist * perp[1])
    ray = LineString([(p.x, p.y), end])

    inside = ray.intersection(polygon)
    if inside.is_empty:
        return 0.0

    # If the centreline is inside the polygon, the intersection is a LineString
    # (or MultiLineString for concave shapes) starting at p.
    if isinstance(inside, LineString):
        return float(inside.length)
    if hasattr(inside, "geoms"):
        # Pick the segment that touches p (the "first" segment along the ray).
        best = 0.0
        for g in inside.geoms:
            if isinstance(g, LineString) and g.distance(p) < 1e-6:
                best = float(g.length)
                break
        if best > 0.0:
            return best
        # Fallback: smallest-distance endpoint (rare concave case).
        return min((float(g.length) for g in inside.geoms if isinstance(g, LineString)),
                   default=0.0)
    return 0.0


# ---------------------------------------------------------------------------
# Run-polygon construction
# ---------------------------------------------------------------------------

def build_run_strip(
    line: LineString,
    stations: list[float],
    inner_offsets: list[float],
    outer_offsets: list[float],
    side: Side,
) -> Polygon:
    """Construct a run polygon by sweeping inner and outer offset points along
    ``stations`` on the given ``side`` of ``line``.

    All offsets are non-negative magnitudes (metres). The perpendicular
    direction is set by ``side``. Output is a CCW-oriented polygon.
    """
    if not (len(stations) == len(inner_offsets) == len(outer_offsets)):
        raise ValueError("stations, inner_offsets, and outer_offsets must be the same length")
    if len(stations) < 2:
        raise ValueError("Need at least 2 stations to build a strip")

    inner_pts: list[tuple[float, float]] = []
    outer_pts: list[tuple[float, float]] = []
    for s, d_in, d_out in zip(stations, inner_offsets, outer_offsets):
        p = line.interpolate(s)
        t = tangent_at_station(line, s)
        perp = perpendicular_unit(t, side)
        inner_pts.append((p.x + d_in * perp[0], p.y + d_in * perp[1]))
        outer_pts.append((p.x + d_out * perp[0], p.y + d_out * perp[1]))

    ring = inner_pts + list(reversed(outer_pts))
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    poly = Polygon(ring)
    if not poly.is_valid:
        poly = poly.buffer(0)  # heal minor self-touches
    return orient_polygon(poly, sign=1.0)


def offset_centerline(
    line: LineString,
    stations: list[float],
    offsets: list[float],
    side: Side,
) -> LineString:
    """Build a polyline parallel to ``line`` whose distance varies per station."""
    pts: list[tuple[float, float]] = []
    for s, d in zip(stations, offsets):
        p = line.interpolate(s)
        t = tangent_at_station(line, s)
        perp = perpendicular_unit(t, side)
        pts.append((p.x + d * perp[0], p.y + d * perp[1]))
    return LineString(pts)
