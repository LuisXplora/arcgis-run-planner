# ADR 0003 — Coordinate reference system conventions

**Status:** Accepted
**Date:** 2026-05
**Context:** Phase 0 scaffolding

## Context

Run widths are measured in metres. Geographic coordinate systems (e.g., WGS84, EPSG:4326) measure positions in degrees, where one degree of longitude varies in metric length with latitude. Computing offsets in degrees produces wrong runs that look right at small scale and break catastrophically at the project scale we care about (a 10 cm width error is unacceptable).

## Decision

The engine accepts polygon and polyline inputs in **projected coordinate systems only**, with units of metres. Geographic CRS inputs are rejected at the API boundary with a clear error.

For Australian projects, the recommended default is **MGA2020** (Map Grid of Australia 2020), with the appropriate zone for the project location:

| State | MGA Zone | EPSG |
|---|---|---|
| WA (Perth) | 50 | 7850 |
| NT, SA central | 53 | 7853 |
| QLD central, NSW west | 55 | 7855 |
| QLD east, NSW east, VIC, ACT, TAS | 56 | 7856 |

For non-Australian projects, any local projected CRS with metre units is acceptable (UTM zones, state plane, etc.).

The engine stores the CRS as an EPSG code on the `WorkArea` and validates that the `ControlString` shares the same CRS. Reprojection is **not** the engine's responsibility — callers (web app, Pro toolbox, agent) handle that before invocation.

## Consequences

**Positive:**

- Engine math is unambiguous; widths are real metres.
- Reprojection logic is centralised in the callers, where it belongs.
- Errors caught at the API boundary, not silently in the geometry.

**Negative:**

- Web app must reproject from web-mercator (EPSG:3857) drawing to MGA before calling the engine. This adds a step but is a one-time integration.
- Cross-zone projects need to pick a single zone; this is a planner judgement call, not an engine problem.

## References

- ICSM technical manual, MGA2020 specification.
- PROJ documentation on transformations between WGS84 and MGA2020.
