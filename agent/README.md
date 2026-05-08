# `agent/` — AI layer for the Run Planner

This package sits *above* the deterministic engine. Per [ADR 0001](../docs/adr/0001-engine-agent-split.md), the agent layer:

- never computes geometry directly
- consumes the engine's structured output (`RunPlan` dataclass)
- produces human-readable narrative, decision support, or interactive workflows
- depends on the engine, but the engine never imports from here

## Modules

| Module | Status | Purpose |
|---|---|---|
| `run_plan_explainer.py` | ✅ Phase 1 | Turn a `RunPlan` into a 3-paragraph narrative explanation for a PE |
| `diagnostics_translator.py` | ⏳ Phase 4 | Translate engine `Diagnostic` items into engineer-actionable advice |
| `constraint_reviewer.py` | ⏳ later | Suggest alternative constraint sets via tool-use |

## Design principles (carried from the AI Upskilling Framework)

1. **Grounding by default.** The system prompt explicitly forbids invention. The model narrates what the engine produced and nothing else.
2. **Injectable client.** Every entry point accepts a `client` callable so the module is testable without an API key. The default factory builds a real `Anthropic` client lazily.
3. **No proprietary data in prompts.** Only synthetic / sample data goes through this layer. See `data/samples/` for fixtures.
4. **Failure is visible.** Missing API key → loud `RuntimeError`. Missing SDK → loud `RuntimeError`. Never a silent fallback to a different model or an empty response.

## Running it

```bash
# from repo root
export ANTHROPIC_API_KEY="sk-ant-..."
python examples/explain_rectangle_plan.py
```

For tests, no API key is required — the test suite stubs the client.

## Future direction

Stage 1 (this module) is structured-input → narrative-output, no tool calls. Stage 2 (Month 3 milestone) introduces tool-use so an agent can call `compute_runs` with alternative constraints to explore the design space. Stage 3 (Month 4) adds a cross-model verification step on the explainer's own output, closing the validation pyramid.
