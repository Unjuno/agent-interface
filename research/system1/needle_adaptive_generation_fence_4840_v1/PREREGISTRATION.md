# Needle adaptive generation fence â Issue #4840

## H/T/D/C/U

**H.** A validation envelope bound to active generation, intent, scope, evidence generation, committed update lineage, valid calibration and adapter digest rejects stale/replayed proposals following activation or rollback while admitting valid current-generation proposals. A confidence-only comparator admits directed stale/invalid proposals.

**T.** Allocation `needle-adaptive-generation-fence-4840-v1`; Issue #4840; branch `research/needle-adaptive-generation-fence-4840-v1-20260927`; additive path `research/system1/needle_adaptive_generation_fence_4840_v1/`. Current-generation state is generation 2 after activation at generation 1 and rollback into a new generation 2. Build exactly 64 rows: eight each for CURRENT_VALID, OLD_INFLIGHT_AFTER_SWITCH, DELAYED_OLD_REPLY, REPLAYED_PRE_ROLLBACK_GENERATION, FUTURE_GENERATION, INTENT_MISMATCH, SCOPE_OR_EVIDENCE_MISMATCH, UPDATE_LINEAGE_OR_CALIBRATION_INVALID. Compare confidence-only threshold .90 against strict validation envelope. Run 15 malformed/stale mutation controls. Candidate output is proposal-only. Trainer container invocation exactly once, separate auditor invocation exactly once, no training updates.

**D.** PASS requires independent exact agreement 64/64, 0/56 unsafe eligibility, 0/8 known-good false YIELD, confidence-only negative eligibility >=40/56, all 15 controls YIELD with zero state mutation/authority, audit errors=0. Typed unsafe-admission FAIL, overrefusal FAIL, comparator HOLD and provenance/environment STOP are in `FREEZE.json`.

**C.** Directed authored cases are contract controls, not an estimate of natural stale-proposal prevalence. The comparator is deliberately confidence-only. Equality and metadata checks do not provide cryptographic authenticity; the experiment is a finite protocol fixture, not an integrated runtime.

**U.** No model training/quality, Astra feedback, GUI, task effect, concurrency, actual filesystem durability, real process race, latency benefit, authorization or product result.

## Frozen container

Cached `needle-pilot05:local`, image ID `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`, Linux/amd64, network none, read-only root and source, 1 CPU, 2 GiB, 64 PIDs, no-new-privileges. Docker version 29.8.0 client/server. Construction-only Docker tests: 11 passed; zero optimizer updates. The initial construction test failure caused by encoding NaN in strict JSON was retained and fixed before freeze by replacing it with a non-numeric confidence control.

Exact source hashes and all gates are in `FREEZE.json`. Formal runs only after remote branch readback matches those bytes. No retry or post-result edit.
