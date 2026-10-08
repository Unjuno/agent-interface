# MAP01 continuation-guard window T2 — retained-data diagnostic

## H/T/D/C/U

- **H:** If the boundary-admissible continuation at health 85 (the separate #6008 finite result) were re-armed under the recovery predicate `fresh typed sequence AND observed health >= source health`, the retained v39 decision-2 trace would force that hypothetical guard to reject before the model answered. Measure when the first rejection evidence became available and how much of the model wait remained.
- **T:** Read only the SHA-pinned v39 `report.json`, `runtime/events.jsonl`, and retention manifest. Select decision 2's frozen model interval and final-action source (sequence 70, health 85); scan typed observations captured during that interval, in order, for non-fresh sequence, unavailable health, or health below 85. A candidate writes one raw summary; a separate raw-only auditor recomputes it. Run four synthetic boundary tests.
- **D:** `PASS_RETAINED_WINDOW_DIAGNOSTIC` only if all pinned hashes match, the first guard-rejection evidence is exactly sequence 76 / health 82, and its typed-event emission is 1,503,225,914 ns after model start, leaving 4,803,647,908 ns before model end. No rejection before answer is `NO_GUARD_REJECTION_OBSERVED`, not PASS. Any source or expected-row mismatch is FAIL.
- **C:** The v39 runtime used unauthored coast for this wait. This is a counterfactual timing overlay, not an actually admitted or executed continuation/recovery policy. The event trace records typed availability, not guard scheduling or physical key-up.
- **U:** No claim about actual recovery action, controller cancellation latency, per-key occupancy, threat-relative suitability, safety, efficacy, survival, or MAP01 completion. No new model/game/GUI/input/container/network operation. The original live result is not rerun or modified.

## Frozen inputs

- Base main: `e12e4e2939890d735cb1b11df3a8d8b6a1cf4b9a`.
- Retained run: `map01-v39-coast-liveness-live-01`.
- `report.json` SHA-256: `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687`.
- `retention-manifest.json` SHA-256: `8dfbac52c298d865b4484aaa51dc0d821bb0d74f8c5995d3117206a1ed0dbda2`.
- `runtime/events.jsonl` SHA-256: `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381`.
- Prior finite boundary evidence: PR #6008, which found continuation admissible at exactly health 85 while primary action was refused. It granted no input authority and no live claim.

## Procedure / stop rules

1. Execute the four synthetic tests before candidate analysis; they must cover an observed drop, unavailable health, non-fresh sequence, and no rejection.
2. Candidate validates the retention manifest and three frozen file hashes before parsing. One invocation, no retries.
3. Independent auditor reads original sources and candidate raw output without importing candidate code. One invocation only after candidate exit 0.
4. Preserve all results even on failure. No image pull/build or shared-resource allocation: this standard-library raw-data transformation has no container-dependent behavior, and container use would not improve the evidence boundary.
