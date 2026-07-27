# Run Planner UI — Quick Start

A browser-based test surface for the run-plotting engine. Pick a sample work area, set width
constraints, generate a run plan, and download the result as GeoJSON. No ArcGIS Pro required.

**Scope (Level 1 beta):** fixture selection + constraints in, plotted run plan + GeoJSON out.
No free-hand polygon drawing, no crews/plant/scheduling — those are separate, later work.

## 1. Setup

Requires Python 3.11+.

```bash
git clone https://github.com/LuisXplora/arcgis-run-planner.git
cd arcgis-run-planner
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

## 2. Run it

```bash
streamlit run ui/streamlit_app.py
```

This opens a browser tab at `http://localhost:8501`. Leave the terminal running; closing it
stops the app.

## 3. Using the app

1. **Work-area fixture** (sidebar) — choose one of four bundled sample sites: Rectangle,
   Trapezoid (both symmetric), Taxiway tie-in (asymmetric), or Runway shoulder
   (edge-referenced).
2. **Mode** — auto-selected to match the fixture; override only if you want to see how the
   engine handles a mismatched mode/geometry pairing (it will report a diagnostic rather than
   crash).
3. **Width constraints** — `w_min` / `w_pref` / `w_max` in metres, plus `station_step_m`
   (sampling interval along the control line). Defaults are sensible milling/paving widths.
4. **Advanced** (optional) — `taper_max` (max width change per metre) and `runs_locked` (force
   a specific run count instead of letting the solver choose; leave at 0 for auto).
5. Click **Generate**. The app renders the run-plan map, prints a text summary (run count,
   coverage %, per-run widths/lengths), and surfaces any engine diagnostics as
   info/warning/error banners.
6. Click **Download GeoJSON** to save the run polygons for use elsewhere (GIS software, further
   scripting, etc.).

## 4. Troubleshooting

- **Blank page / connection refused** — confirm the terminal still shows the `streamlit run`
  process active; re-run the command if it exited.
- **`ModuleNotFoundError`** — the venv isn't activated, or `pip install -e .` didn't complete.
  Re-run step 1.
- **A fixture/mode combination produces zero runs or an error banner** — this is the engine
  correctly flagging an infeasible geometry/constraint combination, not a bug. Try a different
  fixture or widen `w_min`/`w_max`.
