# Successor audit preregistration — Issue #6710

Allocation: `PERSISTENCE-GATED-OPTIONAL-THROTTLE-6650-CONTROL-REPLAY-20261002-01`  
Parent result: #6650 T0 / PR #6670, immutable `FAIL_HYPOTHESIS`  
Additive path: `research/analysis/persistence_gated_throttle_6650_control_replay_20261002_01/`  
Type: independent posthoc raw-only controller-law replay; no new candidate run.

## H / T / D / C / U

**H.** An independently implemented finite event replayer can reproduce the full decision record for every one of the nine retained trace fixtures and four policy arms, including request gating, observable state, controller transitions, service order, deadlines, generation invalidation, and mandatory work. It may reveal discrepancies hidden by the predecessor's accounting-only audit.

**T.** Verify the predecessor fixture and raw hashes from PR #6670's manifest. Implement a separate event-loop reconstruction from those two immutable inputs; do not import or invoke predecessor `candidate.py` or `auditor.py`. Compare all expected fields exactly. Also mutate nine distinct decision/output points and require rejection: tier-at-offer, signal, transition time, suppression choice, session identity, mandatory admission, service order, generation-at-start, and freshness terminal. No candidate re-execution, parameter adjustment, trace modification, or model/GUI/user-data run. Formal invocation budget: candidate 0, independent auditor 1, retry 0. Run the frozen auditor once in a network-disabled OrbStack container with read-only source, separate writable output, digest-pinned cached image, and configured CPU/memory bounds. Record exact engine/image/platform/kernel and command/exit/hash. The host construction suite is preparatory, not the formal result.

**D.** `PASS_AUDIT_REPLAY_SCOPED` only if all 9×4 raw policy outputs exactly equal the independent reconstruction and all nine mutations are rejected; source hashes must match the freeze manifest. Any field mismatch is `FAIL_AUDIT_REPLAY` with paths and original bytes retained. Missing source integrity or a launch/runtime failure is STOP/HOLD, never scientific PASS. This audit result neither changes #6650's adverse hypothesis result nor establishes utility of age-based throttling.

**C.** The replayer can share conceptual assumptions with its predecessor even if separately implemented; finite schedules do not prove untested states. An exact replay can validate code/output conformance while missing a flaw common to both specifications.

**U.** Synthetic authored traces only. No actual queue, planner, live task, user value, safety, performance, or product claim.

## Pre-run freeze

The original package is read-only input. Hashes and this independent implementation are frozen before the sole container auditor invocation. No container candidate is required: this is specifically an audit-only successor, and the source candidate is not executed. Any mismatch/control failure is retained; no fix-and-rerun within this allocation.
