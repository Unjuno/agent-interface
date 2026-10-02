# Issue #2476 — evidence-complete cumulative-drift construction r3

Allocation: `issue2476-track-cumulative-drift-evidence-construction-r3-20260928`.
This is a fresh synthetic construction after r2's immutable auditor failure; it does not reinterpret or modify r1/r2.

## H / T / D / C / U

**H.** Explicitly recording `physical_input_emitted: false` on every scheduled row, including suffix hops skipped after a fail-closed stop, lets an independent raw auditor verify the bounded cumulative-drift construction without treating missing evidence as a negative event.

**T.** Ten fixed synthetic trajectories × two fixed policies × three scheduled hops (60 rows). Reuse the declared case geometries, 8 px local corridor, 12 px global cap, score/margin, age, geometry and sequence limits. Runner generates all scheduled rows and annotates every row with a literal boolean emission field. A separately implemented auditor reconstructs expected decisions from frozen cases and rejects missing/true emission fields, missing rows, and reordering. Audit tests run before the construction invocation.

**D.** `PASS_CUMULATIVE_DRIFT_EVIDENCE_CONSTRUCTION_ONLY` only when all 60 rows reconcile; exact and 12 px boundary cases continue 3/3 under both policies; the repeated 8 px residual case continues under per-hop-only and stops at hop 2 under bounded policy; the 13 px chain stops at hop 3 under bounded policy; all invalidation controls stop at the expected step; every emission flag is literal false; the independent audit has no errors; and all four corruption controls reject.

**C.** Deterministic standard-library Python in local Docker `python:3.13.5-slim-bookworm`, pinned by image ID, network disabled, read-only source/root, bounded resources and separate runner/audit output. No game, GUI, X11, matcher, OS input, provider/model, randomness, previous raw data, or GitHub Actions experiment.

**U.** This only verifies a synthetic state/evidence boundary. It does not establish visual tracking, target identity, real task effect, physical input/release safety, optimality of 12 px, or formal #2476 BASELINE/TRACKED/ABSTAIN benefit. Formal allocation count remains zero.

## Stop rules

All sources, fixture bytes, commands and decisions are frozen before execution. Any identity mismatch, nonempty output, Docker error, audit error, or failed control is retained as the first outcome; no repair, retry, replacement, or post-result tuning in this allocation.
