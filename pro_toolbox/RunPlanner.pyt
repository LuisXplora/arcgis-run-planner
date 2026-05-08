"""ArcGIS Pro Python Toolbox — Run Planner (STUB).

This is the thin ArcPy adapter described in ADR 0002. It converts ArcPy
geometries to Shapely, calls the engine, and converts results back.

Phase 1c status: parameter wiring + adapter shape, no end-to-end execute()
yet. Use as a template; flesh out execute() once the engine API is stable.

To install in ArcGIS Pro:
  1. Project pane > Toolboxes > Add Toolbox > select RunPlanner.pyt
  2. The "Plan Runs (Symmetric)" tool will appear inside.
"""

import importlib
import os
import sys

# arcpy is only available inside ArcGIS Pro's Python.
try:
    import arcpy
except ImportError:  # pragma: no cover
    arcpy = None  # allow file to be parsed outside Pro

# Add the repo root to sys.path so the engine package can be imported.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_THIS_DIR)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)


class Toolbox:
    def __init__(self):
        self.label = "Run Planner"
        self.alias = "run_planner"
        self.tools = [PlanRunsSymmetric]


class PlanRunsSymmetric:
    """Compute a symmetric-mode run plan for a polygon work area and
    centreline polyline."""

    def __init__(self):
        self.label = "Plan Runs (Symmetric)"
        self.description = (
            "Given a polygon work area and a control-string polyline, generate "
            "a symmetric run plan with constraint-driven widths."
        )
        self.canRunInBackground = False

    def getParameterInfo(self):
        params = [
            arcpy.Parameter(
                displayName="Work area polygon",
                name="work_area",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input",
            ),
            arcpy.Parameter(
                displayName="Control string (centreline)",
                name="control_string",
                datatype="GPFeatureLayer",
                parameterType="Required",
                direction="Input",
            ),
            arcpy.Parameter(
                displayName="Minimum run width (m)",
                name="w_min",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input",
            ),
            arcpy.Parameter(
                displayName="Maximum run width (m)",
                name="w_max",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input",
            ),
            arcpy.Parameter(
                displayName="Preferred run width (m)",
                name="w_pref",
                datatype="GPDouble",
                parameterType="Required",
                direction="Input",
            ),
            arcpy.Parameter(
                displayName="Output run feature class",
                name="out_runs",
                datatype="DEFeatureClass",
                parameterType="Required",
                direction="Output",
            ),
        ]
        params[2].value = 2.7
        params[3].value = 4.5
        params[4].value = 3.5
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return

    def execute(self, parameters, messages):
        # Phase 1c stub. The full implementation will:
        #   1. Read the work_area and control_string features via arcpy.da.
        #   2. Convert ArcPy geometries to Shapely (e.g., via WKT).
        #   3. Build WorkArea and ControlString from the engine.
        #   4. Call engine.compute_runs(...).
        #   5. Write each Run.polygon to the output feature class with
        #      attributes for side, ordinal, w_start, w_end, length, area.
        #
        # See examples/plan_rectangle.py for the engine call pattern.
        engine = importlib.import_module("engine")
        messages.addMessage(f"Engine loaded: v{engine.__version__}")
        messages.addWarningMessage(
            "execute() is a Phase 1c stub — geometry conversion not yet wired up. "
            "Use examples/plan_rectangle.py for end-to-end planning today."
        )
        return
