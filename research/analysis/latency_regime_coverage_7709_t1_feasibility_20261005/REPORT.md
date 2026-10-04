# Issue #7709 T1 — retained-trace feasibility (2026-10-05)

## Decision

**HOLD_TOO_FEW_INDEPENDENT_RUNS.** Existing evidence does not justify T2 segment-aware inference. This is a feasibility finding, not a statement that the route effect is absent.

## H / T / D / C / U

**H.** Existing retained route evidence may contain enough independent prepared runs and comparable route/task/model/timing/censor metadata to support the prospective segment-aware comparison in #7709.

**T.** Read-only audit at `3dbbda05eb8d5067ee2c2969615e472a0f20f562` of the public six-task direct/guarded archive, three older API/CLI/MCP transport-only comparisons, and the #3569 route-host preflight result. Candidate v2 validated the complete archive in memory; an independent auditor rechecked it. No runtime replay, archive extraction, or fresh model call.

**D.** Advance only if multiple independent prepared pairs with complete comparable identity, denominator, censoring and timing metadata exist. Otherwise hold and design fresh prospective capture separately.

**C.** Scoped to the exact pinned public Git evidence listed in `FREEZE.json`; unpublished/local evidence was not searched. The public protocol README is treated as a source claim, not as extra raw trials.

**U.** Whether fresh prospective runs can meet the gate, or whether an authorized live allocation becomes available, remains unknown.

## Evidence

- Public archive manifest and all **1,051/1,051** archived file byte counts and SHA-256 values validated.
- The model-visible comparison contains **12 exact-once task rows**, six per route, task IDs 1–6. The observed order is fixed direct-then-guarded. Both goals share seed 992004. Timing fields exist, and host-event sequence/timestamps are ordered, but run/session/prepared-pair identity is absent.
- Exactly one task (direct task 6) lacks `visual_completion_cue_in_save_image`; this weakens its endpoint evidence but does not change the independent-pair count of one.
- Three older comparisons each have one API, one CLI and one MCP transport observation. Their manifests report zero model calls and zero input actions. They measure unlike transport boundaries and are not eligible to pool with model/task outcomes or with one another as matched route trials.
- #3569 is `STOP_CONTAINER_PREFLIGHT` / `STOP_MODEL_ROUTE_UNAVAILABLE`, with zero task calls, model calls and route calls; it is not a zero-latency sample.

## Interpretation and next gate

Only one exploratory serial route pair is available; it cannot estimate between-run/session variation or validate segment-level coverage. The previous #7709 T0 synthetic interval experiment ([report](../latency_regime_coverage_7709_t0_20261005/REPORT.md)) evaluates interval behavior under synthetic assumptions; it does not repair this empirical identity/replication deficit. Therefore no historical-data T2 or route-performance claim is warranted. A future experiment needs preregistered independent pair/session IDs, matched and counterbalanced route order, complete attempt/censor denominators, stable model/task/build identity, and segment endpoints captured before data collection. Any live allocation remains subject to the repository’s ownership gate.

## Execution record

Candidate v1 emitted a misleading preliminary result because it looked up two evidence fields under incorrect names. That output is preserved as `RESULT.json` and explicitly superseded; it was not accepted as evidence. Candidate v2 corrected the schema mappings and produced `RESULT_V2.json`; independent review passed in `AUDIT_V2.json`. See `RUN.md` for exact checks and `SHA256SUMS` for artifact hashes. No container was needed for this source-only Git-object audit.
