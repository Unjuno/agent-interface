# Issue #5273 T0 — verifier compatibility preflight

## H/T/D/C/U

- **H:** A versioned, authority-neutral descriptor snapshot can reject an incompatible plan before any verifier dispatch, while preserving unavailable state and marking costs as estimates.
- **T:** Eight frozen plans: one warm feasible CPU route; unsupported primitive; wrong role; stale version; unavailable GPU placeholder; cold budget violation; prohibited external side effect; infeasible deadline. Compare every status/reason against a literal independent oracle. Verify zero dispatches and authority=`none`.
- **D:** Construction PASS only if exact case IDs, status and reason sets match, no dispatch occurs, and every result retains authority/cost provenance invariants. Formal container result requires a separately granted resource allocation; host execution is not substituted for it.
- **C:** The descriptor snapshot and synthetic costs may be stale or machine-inappropriate. Conservative unavailability may hide a viable backend.
- **U:** This is preflight metadata only. No verifier correctness, scheduler benefit, measured latency, concurrency behavior, runtime integration, or action authority is tested. The existing #5268 IR remains unchanged; its deadline is an integer without a unit, and #5269 profiles are caller-supplied rather than a registry.

## Non-overlap

This is serial, no-call compatibility checking and does not dispatch the #5272 parallel fan-out simulator or use its scheduling workloads. Exact additive path: `research/verification/verifier_registry_5273_t0_v1/`.
