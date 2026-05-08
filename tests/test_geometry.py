"""Unit tests for geometry helpers."""

from __future__ import annotations

import math

import pytest
from shapely.geometry import LineString, Polygon

from engine.geometry import (
    distance_to_boundary,
    perpendicular_unit,
    sample_stations,
    tangent_at_station,
)
from engine.models import Side


def test_sample_stations_includes_endpoints():
    line = LineString([(0, 0), (100, 0)])
    stations = sample_stations(line, step_m=20)
    assert stations[0] == 0.0
    assert stations[-1] == pytest.approx(100.0)
    assert all(s2 > s1 for s1, s2 in zip(stations, stations[1:]))


def test_sample_stations_short_line():
    line = LineString([(0, 0), (3, 0)])
    stations = sample_stations(line, step_m=10)
    assert stations == [0.0, 3.0]


def test_tangent_horizontal_line():
    line = LineString([(0, 0), (10, 0)])
    tx, ty = tangent_at_station(line, s=5.0)
    assert tx == pytest.approx(1.0, abs=1e-6)
    assert ty == pytest.approx(0.0, abs=1e-6)


def test_tangent_diagonal_line():
    line = LineString([(0, 0), (3, 4)])
    tx, ty = tangent_at_station(line, s=2.5)
    assert tx == pytest.approx(0.6, abs=1e-6)
    assert ty == pytest.approx(0.8, abs=1e-6)
    assert math.hypot(tx, ty) == pytest.approx(1.0, abs=1e-6)


def test_perpendicular_unit_left_right():
    # tangent +x => left = +y, right = -y
    assert perpendicular_unit((1.0, 0.0), Side.LEFT) == pytest.approx((0.0, 1.0))
    assert perpendicular_unit((1.0, 0.0), Side.RIGHT) == pytest.approx((0.0, -1.0))


def test_distance_to_boundary_centred_in_rectangle():
    poly = Polygon([(0, 0), (100, 0), (100, 14), (0, 14)])
    line = LineString([(0, 7), (100, 7)])
    d_left = distance_to_boundary(line, s=50.0, polygon=poly, side=Side.LEFT)
    d_right = distance_to_boundary(line, s=50.0, polygon=poly, side=Side.RIGHT)
    assert d_left == pytest.approx(7.0, abs=1e-3)
    assert d_right == pytest.approx(7.0, abs=1e-3)


def test_distance_to_boundary_off_centre():
    poly = Polygon([(0, 0), (100, 0), (100, 14), (0, 14)])
    line = LineString([(0, 4), (100, 4)])  # 4 m from bottom, 10 m from top
    d_left = distance_to_boundary(line, s=50.0, polygon=poly, side=Side.LEFT)
    d_right = distance_to_boundary(line, s=50.0, polygon=poly, side=Side.RIGHT)
    assert d_left == pytest.approx(10.0, abs=1e-3)
    assert d_right == pytest.approx(4.0, abs=1e-3)


def test_distance_to_boundary_trapezoid_taper():
    # Trapezoid widening from 14 m at x=0 to 18 m at x=100, centred on y=8.
    poly = Polygon([(0, 1), (100, -1), (100, 17), (0, 15)])
    line = LineString([(0, 8), (100, 8)])
    # At s=0:   d should be 7 m on each side
    assert distance_to_boundary(line, 0.0, poly, Side.LEFT) == pytest.approx(7.0, abs=1e-2)
    assert distance_to_boundary(line, 0.0, poly, Side.RIGHT) == pytest.approx(7.0, abs=1e-2)
    # At s=100: d should be 9 m on each side
    assert distance_to_boundary(line, 100.0, poly, Side.LEFT) == pytest.approx(9.0, abs=1e-2)
    assert distance_to_boundary(line, 100.0, poly, Side.RIGHT) == pytest.approx(9.0, abs=1e-2)
    # At s=50:  d should be 8 m on each side (linear interpolation)
    assert distance_to_boundary(line, 50.0, poly, Side.LEFT) == pytest.approx(8.0, abs=1e-2)
    assert distance_to_boundary(line, 50.0, poly, Side.RIGHT) == pytest.approx(8.0, abs=1e-2)
