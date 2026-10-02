# Archival report — #5442 T7 corruption-control HOLD

**Disposition:** `HOLD_PREREGISTERED_CORRUPTION_CONTROL_SCOPE_MISMATCH`.
The one-shot candidate and separate WSLc auditor each ran once and exited 0,
but the required target-binding corruption was not exercised: the control
changed `scenario_id`, not the intended target. Do not promote the auditor's
internal `PASS_CONTAINER_REPLAY_SCOPED` label to an overall T7 PASS. Preserve
the raw, audit, inspect receipts, source, and hashes unchanged; do not rerun
T7.

The retained truth table is fixture-authored and deterministic. The WSLc swap
/ cgroup warning remains part of the record; configured memory is not evidence
of enforced limits. No real application observer, GUI effect, runtime
authority, safety rate, or product benefit is established.

The distinct T8 successor in PR #6606 tests an actual serialized
`receipt.intent.target_id` mutation and is already on main. It does not repair
or rewrite T7. Issue #5442 remains open; any further claim must use its own
freshly frozen allocation and preserve this HOLD.
