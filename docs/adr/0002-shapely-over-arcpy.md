# ADR 0002 — Shapely (not ArcPy) as the engine's geometry library

**Status:** Accepted
**Date:** 2026-05
**Context:** Phase 0 scaffolding

## Context

The geometry engine needs vector operations: parallel offsets, polygon clipping, polyline sampling, distance queries, and intersection tests. Two obvious choices:

1. **Shapely (≥2.0).** Pure-Python wrapper over GEOS. Free, widely used in the Python geospatial stack, runs anywhere Python runs.
2. **ArcPy.** Esri's geometry library, distributed with ArcGIS Pro. Best-in-class for some operations and natively understands ArcGIS feature classes.

The system needs to run in three places: a FastAPI service (no ArcGIS install), an ArcGIS Pro Python toolbox (ArcPy available), and a future CI environment (no licensed software).

## Decision

The engine uses **Shapely + NumPy only**. ArcPy is restricted to a thin adapter layer in `pro_toolbox/` that converts ArcPy geometries to Shapely on input and back to ArcPy on output.

## Consequences

**Positive:**

- The engine runs anywhere Python runs — no Esri licence required for development, CI, or the web backend.
- Tests run in plain GitHub Actions without licence-server gymnastics.
- Open-source Shapely API is stable and well-documented.
- Anyone can contribute or fork without buying ArcGIS Pro.

**Negative:**

- Shapely's `parallel_offset` is known to misbehave on tight curves and self-intersecting outputs. We mitigate by validating output and emitting diagnostics rather than silently producing bad geometry.
- We give up some convenience operations that ArcPy provides natively (e.g., `arcpy.cartography.SmoothLine`). For the operations we need, equivalents exist in Shapely or can be implemented in NumPy.

**Revisit if:** The engine is consistently slow on production-sized polygons (>10,000 vertices), or Shapely's offset behaviour blocks core scenarios we cannot work around.

## References

- Shapely 2.0 release notes (vectorised operations, GEOS 3.11+).
- GEOS `BufferOp` / `OffsetCurve` documentation.
