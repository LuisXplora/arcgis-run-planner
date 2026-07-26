"""Pure renderer: turns a RunPlan into a matplotlib Figure."""

from __future__ import annotations

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.figure import Figure
from shapely.geometry import mapping

from engine.models import RunPlan, Side

_SIDE_COLOUR = {Side.LEFT: "#4C72B0", Side.RIGHT: "#DD8452"}


def render_plan(plan: RunPlan) -> Figure:
    """Return a Figure showing the work area, control string, and run polygons.

    Pure: no file I/O, no plt.show().
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    # Work-area outline
    wa_xy = list(plan.work_area.polygon.exterior.coords)
    wa_xs, wa_ys = zip(*wa_xy)
    ax.plot(wa_xs, wa_ys, color="black", linewidth=1.5, label="Work area")

    # Control string (dashed)
    cs_xs, cs_ys = zip(*plan.control.line.coords)
    ax.plot(cs_xs, cs_ys, color="black", linewidth=1.2, linestyle="--", label="Control string")

    # Run polygons
    for run in plan.runs:
        colour = _SIDE_COLOUR[run.side]
        rx, ry = run.polygon.exterior.xy
        ax.fill(rx, ry, alpha=0.5, color=colour, linewidth=0)
        ax.plot(rx, ry, color=colour, linewidth=0.5)
        cx, cy = run.polygon.centroid.x, run.polygon.centroid.y
        ax.annotate(
            str(run.ordinal + 1),
            xy=(cx, cy),
            ha="center",
            va="center",
            fontsize=7,
            color="white",
            fontweight="bold",
        )

    # Legend
    legend_patches = [
        mpatches.Patch(color=_SIDE_COLOUR[Side.LEFT], alpha=0.7, label="Left runs"),
        mpatches.Patch(color=_SIDE_COLOUR[Side.RIGHT], alpha=0.7, label="Right runs"),
    ]
    ax.legend(handles=legend_patches, loc="upper right", fontsize=8)

    ax.set_aspect("equal")
    ax.set_title(
        f"Run plan — {plan.mode.value}  |  {len(plan.runs)} runs  |  "
        f"coverage {100 * plan.coverage_ratio:.1f}%",
        fontsize=10,
    )
    ax.set_xlabel("Easting (m)")
    ax.set_ylabel("Northing (m)")
    fig.tight_layout()
    return fig
