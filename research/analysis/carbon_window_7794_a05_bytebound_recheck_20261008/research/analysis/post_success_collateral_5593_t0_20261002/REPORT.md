# Formal-01 result — post-success collateral T0

Allocation: `POST-SUCCESS-COLLATERAL-5593-T0-20261002-01`  
Related issue: [#5593](https://github.com/Unjuno/agent-interface/issues/5593)  
Scope: synthetic finite event-time accounting only. This is not an empirical agent-interface result.

## Outcome

**PASS_METHOD_SCOPED.** The candidate and a distinct raw-ledger auditor each ran once in separate containers; the auditor reconstructed 5 episodes and 10 horizon rows with no errors. Retries: 0. The frozen source hashes match `FREEZE.json`.

The first-terminal result remains 3 verified successes, 1 verified failure, and 1 policy safe-stop (success fraction 3/5 = 0.6). At launch+3 ticks, bounded clean-success lower/upper fractions are both 3/5 = 0.6. At launch+6 ticks, the lower bound is 1/5 = 0.2 and upper bound 2/5 = 0.4: one success has observed delayed collateral, one has unknown follow-up, and one is clean through the declared horizon. The two non-success first-terminal episodes remain in the all-launched denominator.

This confirms only that the bookkeeping preserves first-terminal outcomes, distinguishes bounded cleanliness from delayed collateral and follow-up uncertainty, and computes the declared synthetic bounds. It does not establish that delayed collateral occurs in real tasks, validate a task contract/oracle, or show product/runtime benefit. `NO_COLLATERAL_COMPLETE` means no collateral observed through that cutoff, never “no collateral ever.”

## Exact formal commands

Both commands used image `python:3.13.5-slim@sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419` with `--network none --read-only --cpus=1 --memory=256m --pids-limit=64 --cap-drop=ALL --security-opt=no-new-privileges --tmpfs /tmp:rw,noexec,nosuid,size=16m`; source was mounted read-only at `/work`, and only `runs/formal-01` was writable at `/out`.

```sh
python /work/runner.py --input /work/fixture.json --output /out/candidate_result.json
python /work/independent_audit.py --input /work/fixture.json --candidate /out/candidate_result.json --output /out/audit_result.json
```

Candidate stdout reported the counts and fractions above and exited 0. Auditor stdout was `{"auditor_invocations": 1, "candidate_and_auditor_separate": true, "errors": [], "reconstructed_episodes": 5, "reconstructed_horizon_rows": 10, "retries": 0, "schema": "post-success-collateral-audit-v1", "status": "PASS_METHOD_SCOPED"}` and exited 0.

## Raw artifact hashes (SHA-256)

- `candidate_result.json`: `38a0150b9c160714e34fd8955d05fa0797d730ae55b0fb9401ffdc187f4d905c`
- `audit_result.json`: `ef954444d4e7e37e88ddad7e124adac3fc2ffe03505d94c2d4e294403629b764`
- `FREEZE.json`: `a4903b861366ac766902cf32260b7bb9426667d788f69409960643435fde24d3`

Formal records are in `runs/formal-01/`. The protocol, frozen inputs, and source hashes are adjacent. Construction checks (10 unit tests, 3 corruption controls, py_compile) are pre-allocation checks, not the formal result.
