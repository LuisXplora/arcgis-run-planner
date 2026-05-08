# ArcGIS Run Planner

> Constraint-driven run-layout engine for milling and paving shift plans on irregular polygon work areas — with an AI-agent layer for ingestion, planning, and explanation.

**Status:** Phase 1a (geometry engine, symmetric mode) — pre-alpha.

---

## What this is

Shift planning for milling (profiling) and paving operations is currently done by sketching runs over Nearmap imagery or scaled CAD PDFs while the dimensional logic lives in a parallel spreadsheet. It is slow, error-prone, and breaks down on non-rectangular geometry (roundabouts, runway thresholds, taxiway tie-ins).

This project builds a geospatial tool that, given:

- a **work-area polygon** (the area to be milled/paved),
- a **control string** (centreline, crown, or edge reference),
- a **mode** (symmetric / asymmetric / edge-referenced),
- and a **constraint set** (min/max run width, preferred width, max taper rate),

produces a structured, geo-referenced **run plan** — one feature per run, with start width, end width, length, area, and centerline geometry — suitable for ArcGIS feature layers and downstream shift spreadsheets.

For the full design see [`docs/SOLUTION_ARCHITECTURE.md`](docs/SOLUTION_ARCHITECTURE.md) (exported from the architecture document).

## Repo layout

```
arcgis-run-planner/
├── docs/
│   ├── adr/                          Architectural Decision Records
│   │   ├── 0001-engine-agent-split.md
│   │   ├── 0002-shapely-over-arcpy.md
│   │   └── 0003-crs-conventions.md
│   └── ROADMAP.md
├── data/
│   └── samples/                      Test fixtures (GeoJSON)
│       ├── rectangle.geojson
│       └── trapezoid.geojson
├── engine/                           Deterministic core package (geometry, solver)
│   ├── models.py                     Dataclasses for inputs/outputs
│   ├── geometry.py                   Offset/clip helpers (Shapely)
│   ├── solver.py                     Run-count + width search
│   ├── engine.py                     Top-level entry point
│   └── modes/
│       ├── symmetric.py              Symmetric-mode planner (Phase 1a — done)
│       ├── asymmetric.py             (stub, Phase 1b)
│       └── edge.py                   (stub, Phase 1b)
├── agent/                            AI layer — sits above the engine (ADR 0001)
│   ├── run_plan_explainer.py         Narrate a RunPlan in plain English
│   └── README.md                     Agent-layer principles and roadmap
├── tests/                            pytest suite (engine + agent)
├── examples/
│   ├── plan_rectangle.py             End-to-end engine example
│   └── explain_rectangle_plan.py     Engine + agent example (needs ANTHROPIC_API_KEY)
├── pro_toolbox/
│   └── RunPlanner.pyt                ArcGIS Pro Python toolbox (stub)
├── .github/workflows/test.yml        CI — lint + tests on push/PR
├── .env.example                      Template for local Anthropic key
├── LICENSE                           MIT
├── pyproject.toml
└── .gitignore
```

## Getting started (on macOS)

```bash
# 1. Clone or open this folder
cd "arcgis-run-planner"

# 2. Create a virtual environment (Python 3.11+)
python3 -m venv .venv
source .venv/bin/activate

# 3. Install the engine in editable mode + dev dependencies
pip install -e ".[dev]"

# 4. Run the tests
pytest

# 5. Run the rectangle example
python examples/plan_rectangle.py
```

If `pip install -e ".[dev]"` complains about Shapely on Apple Silicon, install it first via `pip install shapely` and re-run.

## Phase 1a — what works today

| Capability | Status |
|---|---|
| Symmetric mode on rectangle | ✅ |
| Run-count solver (search for N that minimises width variance) | ✅ |
| Constraint validation (w_min, w_max) | ✅ |
| Run polygons clipped to work area | ✅ |
| Diagnostics block (warnings, infeasibility flags) | ✅ |
| Run Plan Explainer (Claude-backed narrative over engine output, grounded) | ✅ |
| Tapered runs (variable-width) | 🟡 foundation laid in `solver.py`, full impl Phase 1b |
| Asymmetric mode | ⏳ stub only |
| Edge-referenced mode | ⏳ stub only |
| ArcGIS Pro toolbox | 🟡 stub only |
| Diagnostics translator agent | ⏳ planned, Phase 4 |

## Tech choices (one-liners — see ADRs for full rationale)

- **Geometry: Shapely + NumPy.** License-free, well-tested, no ArcPy dependency. ArcPy adapter in the Pro toolbox.
- **CRS: project-local projected (e.g., MGA Zone 56).** Engine rejects geographic CRS to avoid distance-in-degrees errors.
- **Engine ↔ Agent split.** Engine is deterministic and auditable; agent layer (Anthropic SDK) sits above it and never computes geometry directly.

## License

[MIT](./LICENSE) — covers both the engine and the agent layer. The repo is built on personal time with non-sensitive sample data; nothing here is derived from any employer's commercial offering.

## Author

Luis Morales — Project Engineer building toward an AI-systems engineering posture. [LinkedIn](https://www.linkedin.com/in/cpt-luis-morales/) · `cpt.luismorales@gmail.com`
