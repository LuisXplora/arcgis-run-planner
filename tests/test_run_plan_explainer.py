"""Unit tests for the Run Plan Explainer.

The tests do NOT call the Anthropic API. They inject a stub client and
verify two things:

1. The function constructs a prompt that contains the engine's ground-truth
   numbers (so the model has the source it needs — Layer-4 grounding habit).
2. The function returns whatever the client returns (no post-processing
   that could silently mask hallucinations).
"""

from __future__ import annotations

from shapely.geometry import LineString, Polygon

from agent.run_plan_explainer import (
    EXPLAINER_SYSTEM_PROMPT,
    _format_plan_for_prompt,
    explain_run_plan,
)
from engine.models import (
    Constraints,
    ControlString,
    Diagnostic,
    Mode,
    Run,
    RunPlan,
    Severity,
    Side,
    WorkArea,
)


def _make_plan_with_one_run() -> RunPlan:
    """Build a minimal RunPlan in MGA Zone 56 (EPSG:7856) with one run."""
    poly = Polygon([(0, 0), (100, 0), (100, 7), (0, 7)])
    line = LineString([(0, 3.5), (100, 3.5)])
    work_area = WorkArea(polygon=poly, crs_epsg=7856, surface_type="asphalt")
    control = ControlString(line=line, mode=Mode.SYMMETRIC)
    constraints = Constraints(w_min=2.7, w_max=4.5, w_pref=3.5)
    run = Run(
        side=Side.LEFT,
        ordinal=0,
        polygon=Polygon([(0, 0), (100, 0), (100, 3.5), (0, 3.5)]),
        centerline=LineString([(0, 1.75), (100, 1.75)]),
        w_start=3.5,
        w_end=3.5,
        length_m=100.0,
        area_m2=350.0,
    )
    diag = Diagnostic(
        severity=Severity.WARNING,
        code="W001",
        message="taper near limit on run #0",
    )
    return RunPlan(
        work_area=work_area,
        control=control,
        constraints=constraints,
        mode=Mode.SYMMETRIC,
        runs=[run],
        diagnostics=[diag],
    )


def test_format_plan_includes_ground_truth_numbers() -> None:
    plan = _make_plan_with_one_run()
    text = _format_plan_for_prompt(plan)

    # Work-area metadata
    assert "mode: symmetric" in text
    assert "work_area_m2: 700.0" in text
    assert "control_length_m: 100.0" in text

    # Constraint values
    assert "w_min=2.70" in text
    assert "w_pref=3.50" in text
    assert "w_max=4.50" in text

    # Run details
    assert "side=left" in text
    assert "w_start=3.50" in text
    assert "length_m=100.0" in text
    assert "area_m2=350.0" in text

    # Diagnostic surfaced verbatim
    assert "[warning] W001: taper near limit on run #0" in text


def test_format_plan_handles_empty_runs_and_diagnostics() -> None:
    plan = _make_plan_with_one_run()
    plan_no_runs = RunPlan(
        work_area=plan.work_area,
        control=plan.control,
        constraints=plan.constraints,
        mode=plan.mode,
        runs=[],
        diagnostics=[],
    )
    text = _format_plan_for_prompt(plan_no_runs)
    assert "runs (0):" in text
    assert "diagnostics (0):" in text
    assert "(none)" in text


def test_explainer_calls_client_with_grounding_prompt() -> None:
    plan = _make_plan_with_one_run()
    captured: dict[str, str] = {}

    def stub_client(system: str, user: str) -> str:
        captured["system"] = system
        captured["user"] = user
        return "stub narrative"

    result = explain_run_plan(plan, client=stub_client)

    # The function passes the explainer system prompt verbatim
    assert captured["system"] == EXPLAINER_SYSTEM_PROMPT
    # The user prompt contains the engine's serialised plan
    assert "RUN PLAN (engine output, ground truth)" in captured["user"]
    assert "work_area_m2: 700.0" in captured["user"]
    # The function returns the client's response unchanged
    assert result == "stub narrative"


def test_explainer_returns_client_output_verbatim() -> None:
    """No silent post-processing — what the model says is what the caller sees."""
    plan = _make_plan_with_one_run()

    def echo_client(system: str, user: str) -> str:  # noqa: ARG001
        return "  three\nparagraphs  \n  here  "

    # We deliberately don't strip; the client controls its output shape.
    # The default Anthropic client strips, but injected clients are trusted.
    result = explain_run_plan(plan, client=echo_client)
    assert result == "  three\nparagraphs  \n  here  "
