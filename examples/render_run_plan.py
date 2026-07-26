"""Render PNG previews for both sample fixtures.

Run from the repo root:
    python examples/render_run_plan.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from engine import Constraints, Mode, compute_runs
from engine.models import load_geojson_case
from engine.render import render_plan


def main() -> int:
    samples = ROOT / "data" / "samples"
    out_dir = ROOT / "data"

    cases = [
        ("rectangle.geojson", Mode.SYMMETRIC),
        ("trapezoid.geojson", Mode.SYMMETRIC),
        ("taxiway_tiein.geojson", Mode.ASYMMETRIC),
        ("runway_shoulder.geojson", Mode.EDGE_REFERENCED),
    ]

    for case_name, mode in cases:
        stem = Path(case_name).stem
        print(f"\n=== {case_name} ({mode.value}) ===")

        work_area, control = load_geojson_case(samples / case_name, mode=mode)
        constraints = Constraints(w_min=2.7, w_max=4.5, w_pref=3.5)
        plan = compute_runs(work_area, control, constraints)
        print(plan.summary())

        fig = render_plan(plan)
        out_path = out_dir / f"{stem}_plan.png"
        fig.savefig(out_path, dpi=150, bbox_inches="tight")
        print(f"  wrote {out_path.relative_to(ROOT)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
