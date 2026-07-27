"""Streamlit UI for run-plan generation.

Level 1 scope: pick a fixture, set constraints, generate a plan, view/download
it. No drawing, no crew/plant/schedule fields, no persistence. Consumes the
engine's public API only — see engine/__init__.py.
"""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from engine import Constraints, Mode, compute_runs
from engine.models import load_geojson_case, runs_to_geojson
from engine.render import render_plan

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"

# label -> (filename, default mode)
FIXTURES: dict[str, tuple[str, Mode]] = {
    "Rectangle (symmetric)": ("rectangle.geojson", Mode.SYMMETRIC),
    "Trapezoid (symmetric, tapered)": ("trapezoid.geojson", Mode.SYMMETRIC),
    "Taxiway tie-in (asymmetric)": ("taxiway_tiein.geojson", Mode.ASYMMETRIC),
    "Runway shoulder (edge-referenced)": ("runway_shoulder.geojson", Mode.EDGE_REFERENCED),
}

st.set_page_config(page_title="ArcGIS Run Planner", layout="wide")
st.title("ArcGIS Run Planner")

with st.sidebar:
    st.header("Inputs")

    fixture_label = st.selectbox("Work-area fixture", list(FIXTURES.keys()))
    fixture_file, default_mode = FIXTURES[fixture_label]

    mode_options = list(Mode)
    mode = st.selectbox(
        "Mode",
        mode_options,
        index=mode_options.index(default_mode),
        format_func=lambda m: m.value,
    )

    w_min = st.number_input("w_min (m)", value=2.7, step=0.1, format="%.2f")
    w_pref = st.number_input("w_pref (m)", value=3.5, step=0.1, format="%.2f")
    w_max = st.number_input("w_max (m)", value=4.5, step=0.1, format="%.2f")
    station_step_m = st.number_input("station_step_m", value=5.0, step=0.5, format="%.1f")

    with st.expander("Advanced"):
        taper_max = st.number_input("taper_max", value=0.10, step=0.01, format="%.2f")
        runs_locked_input = st.number_input(
            "runs_locked (0 = auto)", value=0, min_value=0, step=1
        )
        runs_locked = runs_locked_input or None

    generate = st.button("Generate", type="primary")

if generate:
    try:
        work_area, control = load_geojson_case(SAMPLES_DIR / fixture_file, mode=mode)
        constraints = Constraints(
            w_min=w_min,
            w_max=w_max,
            w_pref=w_pref,
            taper_max=taper_max,
            runs_locked=runs_locked,
            station_step_m=station_step_m,
        )
        plan = compute_runs(work_area, control, constraints)
        st.session_state["plan"] = plan
    except ValueError as e:
        st.session_state.pop("plan", None)
        st.error(str(e))

plan = st.session_state.get("plan")

if plan is not None:
    fig = render_plan(plan)
    st.pyplot(fig)

    geojson_bytes = json.dumps(runs_to_geojson(plan), indent=2).encode("utf-8")
    st.download_button(
        "Download GeoJSON",
        data=geojson_bytes,
        file_name="run_plan.geojson",
        mime="application/geo+json",
    )

    st.code(plan.summary())

    for d in plan.diagnostics:
        if d.severity.value == "error":
            st.error(f"[{d.code}] {d.message}")
        elif d.severity.value == "warning":
            st.warning(f"[{d.code}] {d.message}")
        else:
            st.info(f"[{d.code}] {d.message}")
else:
    st.info("Set inputs in the sidebar and click Generate.")
