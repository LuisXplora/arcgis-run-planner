# ADR 0001 — Split the geometry engine from the AI agent layer

**Status:** Accepted
**Date:** 2026-05
**Context:** Phase 0 scaffolding

## Context

The system has two responsibilities that look superficially similar but differ in essential character:

1. **Compute runs from a polygon and a control string subject to constraints.** This must be correct, deterministic, auditable, and explainable in geometric terms. Wrong answers here translate to wasted asphalt and missed shifts.

2. **Interpret human intent, ingest messy inputs (CAD PDFs, satellite screenshots, written briefs), propose layout options, and narrate trade-offs.** This benefits from flexibility, language understanding, and the ability to handle inputs we did not anticipate.

A common early mistake when building LLM-powered tools is to conflate these — for example, asking the model to compute offsets directly, or asking the geometry layer to interpret natural language. Both produce systems that are simultaneously fragile and hard to audit.

## Decision

Build the geometry engine as a **deterministic Python package** with a typed, well-tested API. Build the AI agent layer as a **separate component** that sits above the engine and calls it as a tool (in the Anthropic SDK tool-use sense).

Concretely:

- The `engine/` package never imports `anthropic`, never reads natural language, never makes a network call.
- The `agent/` package (future) never computes geometry. It exclusively calls `engine.compute_runs(...)` and reasons over the structured result.

## Consequences

**Positive:**

- The engine is testable with classical unit tests. Geometric invariants are checkable. CI is straightforward.
- The engine is portable: it powers the web app, the ArcGIS Pro toolbox, and any future CLI without modification.
- The agent layer can be replaced, upgraded, or A/B-tested without touching the geometry.
- Auditability: every run plan can be traced to a deterministic engine call with known inputs and version, even if the agent helped pick those inputs.

**Negative:**

- Slightly more boilerplate. The engine API has to be designed; we cannot rely on the agent to paper over rough edges.
- Two packages to maintain.

**Trade-off accepted:** The boilerplate cost is low; the auditability and portability benefits are high and grow over time.

## References

- Anthropic tool-use docs (the pattern this design follows).
- "Building effective AI agents" — Anthropic engineering blog, 2024.
