 Roadmap

Phase definitions and success criteria are pulled from the solution
architecture document. This file is the working tracker.

## Phase 0 — Prep ✅

### Developer environment (do this first, before installing the engine)

- [ ] Install Homebrew (macOS package manager) — https://brew.sh
- [ ] `brew install python@3.12 git` — Python 3.11+ is required by `pyproject.toml`
- [ ] `brew install --cask visual-studio-code` — primary editor
- [ ] VS Code extensions: `ms-python.python`, `ms-python.vscode-pylance`, `charliermarsh.ruff`, `tamasfe.even-better-toml`, `yzhang.markdown-all-in-one`
- [ ] `npm install -g @anthropic-ai/claude-code` — Claude Code CLI for agentic workflows; deliberately part of the AI-fluency upskilling goal, not just a convenience tool
- [ ] GitHub account + SSH key configured (`ssh-keygen -t ed25519` then add public key in GitHub settings)
- [ ] Configure Git identity: `git config --global user.name` / `user.email`

### Repo scaffolding

- [x] Repo scaffolding (`engine/`, `tests/`, `examples/`, `pro_toolbox/`, `docs/`)
- [x] `pyproject.toml`, `.gitignore`, `README.md`
- [x] ADRs 0001 (engine/agent split), 0002 (Shapely vs ArcPy), 0003 (CRS conventions)
- [x] Sample data: rectangle, trapezoid
- [x] `git init` and first commit
- [x] Create the GitHub repo (public — `github.com/LuisXplora/arcgis-run-planner`)

## Phase 1a — Geometry MVP (symmetric mode) ✅ CURRENT

- [x] `engine/models.py` (WorkArea, ControlString, Constraints, Run, RunPlan, Diagnostic)
- [x] `engine/geometry.py` (sample_stations, tangent, perpendicular, distance_to_boundary, build_run_strip)
- [x] `engine/solver.py` (run-count search, infeasibility handling)
- [x] `engine/modes/symmetric.py`
- [x] `engine/engine.py` (top-level dispatch)
- [x] Test suite (geometry, solver, end-to-end rectangle, end-to-end trapezoid)
- [x] `examples/plan_rectangle.py`
- [x] ArcGIS Pro toolbox stub

**Done when:** `pytest` is green on Luigi's Mac.

## Phase 1b — Asymmetric & edge-referenced modes  ← engine work ✅ (2026-07-26)

- [x] `engine/modes/asymmetric.py` — independent N per side *(158 lines, implemented)*
- [x] `engine/modes/edge.py` — control string is one polygon edge *(177 lines, implemented)*
- [x] Sample data: taxiway tie-in (asymmetric), runway shoulder (edge)
- [x] Cross-mode test parity *(`test_asymmetric.py` + `test_edge.py`; full suite 44 passed)*
- [x] Portable PNG renderer (`engine/render.py` + `examples/render_run_plan.py`) — de-risk demo surface *(added ahead of Phase 2)*
- [ ] Pro toolbox `execute()` fully wired (ArcPy ↔ Shapely conversion) ← **only remaining 1b item**

**Done when:** all three modes plan correctly on their fixture cases. Engine ✅; Pro toolbox wiring outstanding.

## Phase 2 — Web app MVP

- [ ] FastAPI service exposing `compute_runs` over HTTP
- [ ] React/TypeScript frontend with ArcGIS Maps SDK for JavaScript
- [ ] Sketch tools (polygon + control string)
- [ ] Constraint form + Generate button + map preview of runs
- [ ] AGOL feature-layer round-trip (read inputs, write run plan)
- [ ] CSV/XLSX export of run schedule

## Phase 3 — Agent layer

- [ ] Anthropic SDK wired in with tool-use
- [ ] Ingestion agent (PDF/imagery → polygon proposal)
- [ ] Planning agent (calls compute_runs with proposed constraints)
- [ ] Explainer agent (narrative from RunPlan + diagnostics)
- [ ] Chat panel in the web app

## Phase 4 — AGOL integration & multi-user

- [ ] OAuth against AGOL (Creator/Publisher account)
- [ ] Project / WorkArea / ControlString / RunPlan as hosted feature layers
- [ ] Shift narratives stored as documents
- [ ] Concurrency tested with two planners

## Phase 5 — Polish & rollout

- [ ] Experience Builder widget
- [ ] LinkedIn post arc (problem / architecture / demo)
- [ ] First live shift uses it

## Open questions tracked elsewhere

- IP framing (personal vs employer) — see architecture §13.
- License choice (likely MIT) — see ADR 0004 (TBD).
