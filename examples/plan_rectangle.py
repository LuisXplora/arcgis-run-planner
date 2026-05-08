"""End-to-end example: load the rectangle fixture, compute a plan, print it.

Run from the repo root:
    python examples/plan_rectangle.py

Or from anywhere with the engine installed:
    python -m examples.plan_rectangle
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Allow running without `pip install -e .`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import Constraints, Mode, compute_runs
from engine.models import load_geojson_case, runs_to_geojson


def main() -> int:
    samples = ROOT / "data" / "samples"

    for case_name in ("rectangle.geojson", "trapezoid.geojson"):
        print(f"\n=== {case_name} ===")
        work_area, control = load_geojson_case(samples / case_name, mode=Mode.SYMMETRIC)
        constraints = Constraints(w_min=2.7, w_max=4.5, w_pref=3.5)
        plan = compute_runs(work_area, control, constraints)
        print(plan.summary())

        out_path = ROOT / "data" / f"{Path(case_name).stem}_plan.geojson"
        with out_path.open("w") as f:
            json.dump(runs_to_geojson(plan), f, indent=2)
        print(f"  wrote {out_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
