# Local relevance gating preflight v1

Issue: #2188
Status: scoped negative/limited result; synthetic-only.

## H / T / D / C / U

- H: a bounded local classifier can filter clearly irrelevant observation updates while yielding ambiguous or stale evidence.
- T: deterministic 32x32 raster fixtures, 4–5 features, tiny logistic model, temporal persistence, held-out calibration, and a second-seed shift check.
- D: single-frame accuracy 65.78%; temporal persistence 81.11% (TP 185, TN 180, FP 67, FN 18). Within-distribution three-state accept precision was 100%. Held-out calibration yielded accept threshold 0.52165 and 33.8% acceptance with zero false accepts on the evaluation half. Applying it to a second seed produced one false accept at 29.4% acceptance. OOD distance flagged 0.39% and did not remove all risk.
- C: no authority is granted to the local classifier. Only bounded high-confidence accept may continue; low-confidence, OOD, stale, or inconsistent evidence must become unknown/YIELD and return to fresh evidence or rich-model reasoning.
- U: no real-GUI, token, latency, gameplay, or portability claim. Synthetic line is stopped until source-bound real frames are available.

## Decision

HOLD_SYNTHETIC_ONLY_DISTRIBUTION_SHIFT_RISK.

This file records the result without changing historical experiments. The next successor must use real captured frames with provenance and explicit YIELD auditing.
