# Execution and audit receipt

Allocation `error-budget-selective-labels-5424-t3-20261001-01` was preregistered on Issue #5424 before the candidate call. Frozen source and fixture identities are in `FREEZE.json`; all six source files were read back from branch `research/5424-selective-labels-t3-20261001` and Git blob SHA-1 values matched local files. Pre-run source syntax checks passed 3/3; candidate and auditor invocations before freeze were both 0; raw output did not exist.

## Commands

Candidate, one invocation:

```text
python3 -B candidate.py
exit 0
{"gates":{"all_offered_rows_retained":true,"censored_never_success":true,"common_cause_fallback_severe_retained":true,"probe_absent_or_stale_stays_censored":true,"probe_policy_no_unsupported_unfreeze":true,"probe_positive_unfreezes_repaired_case":true,"quiet_window_counterexample":true},"rows":160,"status":"CANDIDATE_COMPLETE"}
```

Auditor, one separate process:

```text
python3 -B audit.py
exit 0
{"mismatches":[],"mutation_rejections":4,"status":"PASS_METHOD_SCOPED"}
```

## Auditor corruption controls

The frozen auditor corrupts a copy of the retained raw result in four ways and requires each replay to reject it:

1. Change a frozen/censored primary outcome to `OK`.
2. Change an executed common-cause fallback `SEVERE` to `OK`.
3. Admit the route using the stale-generation positive probe.
4. Omit an offered-task row.

All four were rejected. The retained candidate raw and final audit are `raw_result.json` and `audit_result.json`; their SHA-256 values and the frozen source hashes are recorded in `SHA256SUMS`.

## Boundary

This was a host-only deterministic synthetic simulation, not a Docker/container experiment. No Docker engine was queried or changed; no model/provider, GUI, runtime, real route, user data, GPU, or input was used. It neither allocates nor consumes the separately coordinated #59 live T1 or any shared container slot. The candidate and audit each ran once, with no retries, replacements, or tuning.
