# Allocation 04 — inconclusive dispatch-state STOP

- Allocation: `X11-BACKEND-RESTART-MULTICONTROL-2437-20261001-04`
- Frozen main: `19c588c063fec0cc46ccda5d0154a5984afcb6c1`
- Freeze branch/commit: `research/2437-backend-restart-multicontrol-v4-20261001` / `ea192babc76257a03899ac346e5602bfe2b14d35`.
- Candidate invocation count: **1**, exit 0. Raw-only audit invocation count: **1**.
- Disposition: **`STOP_INCONCLUSIVE_DISPATCH_STATE`**, audit errors 0. Raw length 2,351 bytes; one auditor read recorded SHA-256 `4cfc67e990d400e7395e11f2712d3eea1d32ef33b244e2565befa88c3ea1401f`.
- No scientific PASS/FAIL is inferred. The validated raw gates cover the pre/post-crash multi-control identities and cleanup, but the auditor could not classify whether the replacement request was already quarantined before dispatch.
- Read-only source diagnosis (not raw inspection): V4 assigned `new_session_recovery_required_initial` from `session.recovery_required` after calling `dispatch`; an unverified release can mutate that flag during dispatch. The same post-dispatch value was written into the `after` field, so the auditor cannot reconstruct entry state. V5 isolates a receipt-capture helper and adds a unit test that simulates dispatch mutating recovery state, requiring the `initial=false` and `after=true` values to remain distinguishable.
- V4 raw remains untouched and must not be re-read, re-audited or rerun. Allocation 05 is separately versioned; do not pool outcomes.
- Private WSL Xvfb only; no Docker slot was assigned under #5085.
