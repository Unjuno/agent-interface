# #2766 runtime evidence-compute lattice transfer

## H
The exact #1702 ordering can consume a real source-versioned PNG capture/local-compute ledger without stale reuse, hard-gate override, implicit rebuild execution, or reusable publication after cancellation.

## T
18 fixed first-outcome cases. CACHED_COMPLETE tests exact reuse, deadline expiry, mismatch and mismatch+expiry precedence. ACTIVE_JOB tests measured RUN/WAIT/TIE inputs, stale/tardy hard gates, capture/compute invalidation, partial-before-cancel and deadline crossing. Rebuild tests require a separate measured rebuild cost before a fresh ACTIVE_JOB identity. PNG encoding/decoding, SHA-256, filesystem version mutation and monotonic timings are actual local operations. p/g/w are retained from explicit calibration operations: p is a measured invalidation fraction from source-version probes; g/w are measured wait/compute durations in ns. No model/provider or GUI/input.

Formal order is the exact CASES list in run_case.py, batches 0 then 1. No formal rerun/replacement/pooling or post-freeze scientific tuning.

## D
PASS_EVIDENCE_COMPUTE_LATTICE_RUNTIME_SCOPED requires 18/18 cases, zero candidate/oracle decision mismatch, exact source/version/deadline hard-gate precedence, no implicit REBUILD_REQUIRED execution, no reusable publication after later CANCEL_STALE/CANCEL_TARDY, partial-result retention without reuse, complete process receipts, raw-only audit errors=[], and all 12 copied-evidence corruptions rejected.

FAIL_POLICY_ENFORCEMENT on stale reuse, tardy publication, hard-gate override or rebuild bypass. HOLD_RUNTIME_INPUTS_INCOMPLETE on missing/calibration/source/timestamp/partial classification evidence. STOP on source/process/denominator ambiguity.

## C
Python/filesystem/PNG/zlib scheduling and authored invalidation probes affect absolute timing. The calibration population is diagnostic for this adapter and is not a deployment-rate estimate. #2806 remains the prospective deployment calibration question.

## U
No model/task utility, GUI generality, production threshold, global scheduler optimality, cross-platform timing or token benefit. This tests runtime application of the #1702 order only.
