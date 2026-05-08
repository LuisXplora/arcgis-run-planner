"""End-to-end example: load the rectangle fixture, compute a plan, ask the
Run Plan Explainer to narrate it.

Requires:
    export ANTHROPIC_API_KEY="sk-ant-..."
    pip install -e ".[agent]"

Run from repo root:
    python examples/explain_rectangle_plan.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running without `pip install -e .`
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent import explain_run_plan
from engine import Constraints, Mode, compute_runs
from engine.models import load_geojson_case


def main() -> int:
    fixture = ROOT / "data" / "samples" / "rectangle.geojson"
    work_area, control = load_geojson_case(fixture, mode=Mode.SYMMETRIC)
    constraints = Constraints(w_min=2.7, w_max=4.5, w_pref=3.5)
    plan = compute_runs(work_area, control, constraints)

    print("=== Engine summary (deterministic) ===")
    print(plan.summary())
    print()

    print("=== Explainer narrative (Claude, grounded) ===")
    narrative = explain_run_plan(plan)
    print(narrative)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
