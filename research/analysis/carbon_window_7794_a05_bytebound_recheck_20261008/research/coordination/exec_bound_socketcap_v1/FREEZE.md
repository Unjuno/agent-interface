# Source-first freeze — exec-bound socket capability v1

Task: `COORD-EXEC-BOUND-SOCKETCAP-20260917-025`
Issue: #608
Publication BASE: `8210ddde82f4b01c5d00042afb45fd64e85cd1da`
Formal allocation: `exec-bound-socketcap-20260917-a1`
Scope: `research/coordination/exec_bound_socketcap_v1/**`

Formal source is frozen before any `m*` case. The only intervention is whether the trusted helper's inherited unnamed socket capability survives the helper→task `exec` boundary (`persistent_cap`) or is marked non-inheritable / `FD_CLOEXEC` (`cloexec_cap`). Helper and post-exec task must retain the same PID.

The 12-case schedule in `plan.json` is fixed as six independent two-case chunks to bound outer supervision. No measured ID may be rerun, replaced or extended. A post-decision `B_change` changes only B revision/value. Owner token validation and generation commit are one SQLite `BEGIN IMMEDIATE` transaction.

Excluded construction used only `c*` IDs and is not pooled with formal evidence.
