"""ArcGIS Run Planner — geometry engine.

The engine is deterministic: same inputs in, same runs out. It has no
dependency on Anthropic/agents/networking. See ADR 0001.
"""

from engine.engine import compute_runs
from engine.models import (
    ControlString,
    Constraints,
    Diagnostic,
    Mode,
    Run,
    RunPlan,
    Severity,
    Side,
    WorkArea,
)

__version__ = "0.1.0"

__all__ = [
    "compute_runs",
    "ControlString",
    "Constraints",
    "Diagnostic",
    "Mode",
    "Run",
    "RunPlan",
    "Severity",
    "Side",
    "WorkArea",
    "__version__",
]
