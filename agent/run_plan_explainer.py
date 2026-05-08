"""Run Plan Explainer — first agentic feature on the Run Planner.

Given a RunPlan (produced by the deterministic engine), this module asks
Claude to write a 3-paragraph human-readable narrative for a Project Engineer.

Design principles
-----------------
1. **Grounding (Layer 4, habit #1).** The model is told explicitly to use ONLY
   the structured plan data it is given. It is never asked what it "knows"
   about milling/paving — only to narrate what the engine produced.

2. **No geometry computation in the agent.** Per ADR 0001, the agent layer
   never re-derives quantities. If a number appears in the narrative, it
   came verbatim from the RunPlan dataclass.

3. **Testable without a network.** The function accepts an injectable
   ``client`` callable so unit tests can run with a stub. The default factory
   creates a real Anthropic client lazily — no anthropic import at module
   load time.

This is Stage 1 of the framework's chat → tool-use → agent → multi-agent
progression: structured input → narrative output, no tool calls yet.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Protocol

from engine.models import RunPlan


# --------------------------------------------------------------------------
# Prompt
# --------------------------------------------------------------------------

EXPLAINER_SYSTEM_PROMPT = """\
You are a senior Project Engineer reviewing a milling/paving run plan for a
junior engineer on the same project. You are given the structured output of a
deterministic run-planning engine.

Your job is to narrate the plan in plain English so the junior engineer can
read it once and understand: what the work area is, how the engine has split
it into runs, and whether anything in the diagnostics needs the engineer's
attention before site execution.

Hard rules — these are non-negotiable:

1. Use ONLY the numbers and facts present in the structured plan data below.
   Do NOT invent or infer quantities, materials, or schedule information.
2. If a quantity is not in the data, say "not stated in the plan" rather than
   guessing. Never round generously to fill a sentence.
3. Keep the output to exactly three short paragraphs:
   - Paragraph 1: the work area and overall split (area, control length,
     mode, run count, coverage).
   - Paragraph 2: the run dimensions (widths, lengths, taper if any).
     Mention any individual run that stands out (widest, narrowest, steepest
     taper).
   - Paragraph 3: diagnostics — list any warnings or errors with the
     engineer-facing implication. If diagnostics is empty, say "No
     constraint violations or warnings flagged by the engine." in one line.
4. No headings, no bullet lists, no markdown. Plain prose paragraphs only.
5. Match a working civil engineer's tone — direct, factual, no marketing
   language. No phrases like "exciting," "robust solution," or "leveraging."

If the data appears empty or incoherent, say so plainly in one paragraph
rather than fabricating content.
"""


# --------------------------------------------------------------------------
# Client abstraction
# --------------------------------------------------------------------------

class _SupportsExplain(Protocol):
    """Minimal protocol for an explainer client.

    Any callable matching ``(system: str, user: str) -> str`` qualifies.
    Tests pass a stub; production passes the Anthropic-backed default.
    """

    def __call__(self, system: str, user: str) -> str: ...


def _default_anthropic_client(
    *,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 800,
) -> _SupportsExplain:
    """Build the production client. Imports ``anthropic`` lazily so unit
    tests do not need the SDK installed."""
    try:
        from anthropic import Anthropic  # noqa: WPS433 — lazy import is intentional
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "The 'anthropic' SDK is required for the default explainer client. "
            "Install via: pip install -e \".[agent]\""
        ) from exc

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY environment variable is not set. "
            "Export it in your shell or load it via a .env file."
        )

    client = Anthropic(api_key=api_key)

    def _call(system: str, user: str) -> str:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        # The SDK returns a list of content blocks; we only request text.
        parts = [block.text for block in message.content if block.type == "text"]
        return "\n".join(parts).strip()

    return _call


# --------------------------------------------------------------------------
# Plan serialisation
# --------------------------------------------------------------------------

def _format_plan_for_prompt(plan: RunPlan) -> str:
    """Serialise a RunPlan into the deterministic text block fed to the model.

    The format is intentionally machine-readable-ish but trivially scannable
    by a human, so the prompt itself is auditable.
    """
    lines: list[str] = []
    lines.append("=== RUN PLAN (engine output, ground truth) ===")
    lines.append(f"mode: {plan.mode.value}")
    lines.append(f"work_area_m2: {plan.work_area.area_m2:.1f}")
    lines.append(f"work_area_surface: {plan.work_area.surface_type}")
    if plan.work_area.notes:
        lines.append(f"work_area_notes: {plan.work_area.notes}")
    lines.append(f"control_length_m: {plan.control.length_m:.1f}")
    lines.append(
        "constraints: "
        f"w_min={plan.constraints.w_min:.2f} m, "
        f"w_pref={plan.constraints.w_pref:.2f} m, "
        f"w_max={plan.constraints.w_max:.2f} m, "
        f"taper_max={plan.constraints.taper_max:.3f} m/m"
    )
    lines.append(f"total_run_area_m2: {plan.total_area_m2:.1f}")
    lines.append(f"coverage_pct: {100 * plan.coverage_ratio:.1f}")

    lines.append("")
    lines.append(f"runs ({len(plan.runs)}):")
    if not plan.runs:
        lines.append("  (none)")
    for r in plan.runs:
        lines.append(
            f"  - side={r.side.value} ord={r.ordinal} "
            f"w_start={r.w_start:.2f} m w_end={r.w_end:.2f} m "
            f"length_m={r.length_m:.1f} area_m2={r.area_m2:.1f}"
        )

    lines.append("")
    lines.append(f"diagnostics ({len(plan.diagnostics)}):")
    if not plan.diagnostics:
        lines.append("  (none)")
    for d in plan.diagnostics:
        lines.append(f"  - [{d.severity.value}] {d.code}: {d.message}")

    return "\n".join(lines)


# --------------------------------------------------------------------------
# Public entry point
# --------------------------------------------------------------------------

def explain_run_plan(
    plan: RunPlan,
    *,
    client: Callable[[str, str], str] | None = None,
) -> str:
    """Produce a 3-paragraph narrative explanation of a run plan.

    Parameters
    ----------
    plan : RunPlan
        The structured output from ``engine.compute_runs``.
    client : callable, optional
        A function ``(system, user) -> str`` that calls a language model.
        Defaults to a lazily-constructed Anthropic client. Tests inject a
        stub here.

    Returns
    -------
    str
        Three paragraphs of plain prose, no markdown, matching the rules in
        ``EXPLAINER_SYSTEM_PROMPT``.

    Raises
    ------
    RuntimeError
        If the default client is requested but ``ANTHROPIC_API_KEY`` is not
        set, or the ``anthropic`` SDK is not installed.
    """
    if client is None:
        client = _default_anthropic_client()

    user_prompt = _format_plan_for_prompt(plan)
    return client(EXPLAINER_SYSTEM_PROMPT, user_prompt)
