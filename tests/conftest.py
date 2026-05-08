"""Pytest configuration.

Adds the repo root to sys.path so tests can run via `pytest` even when the
engine is not pip-installed.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from engine.models import Constraints, ControlString, Mode, WorkArea, load_geojson_case


SAMPLES_DIR = ROOT / "data" / "samples"


@pytest.fixture
def rectangle_case() -> tuple[WorkArea, ControlString]:
    return load_geojson_case(SAMPLES_DIR / "rectangle.geojson", mode=Mode.SYMMETRIC)


@pytest.fixture
def trapezoid_case() -> tuple[WorkArea, ControlString]:
    return load_geojson_case(SAMPLES_DIR / "trapezoid.geojson", mode=Mode.SYMMETRIC)


@pytest.fixture
def default_constraints() -> Constraints:
    return Constraints(
        w_min=2.7,
        w_max=4.5,
        w_pref=3.5,
        taper_max=0.10,
        station_step_m=5.0,
    )
