"""Agent layer for the Run Planner.

Per ADR 0001 (engine/agent split), this package sits *above* the engine. It
must never compute geometry directly; it consumes the engine's structured
output and produces human-readable narrative or interactive workflows.

Public surface:
    explain_run_plan: turn a RunPlan into a 3-paragraph narrative.
"""

from agent.run_plan_explainer import explain_run_plan

__all__ = ["explain_run_plan"]
