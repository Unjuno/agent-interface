# Paired T1 adjudicator construction v2 — identity validation precedence

Status: pre-freeze. Successor to the immutable FAIL_AUDIT at `decision_rule_construction_v1/` and GitHub Issue #5658 / PR #5660. This is synthetic decision-code construction, not the live #59 allocation.

## H / T / D / C / U

- **H:** An adjudicator that validates each identity's syntax before comparing session identity equality will classify malformed identities as `identity_format:<field>` regardless of cross-session mismatch, while retaining all 729 directional decisions from v1 and rejecting all frozen safety/integrity controls.
- **T:** Pin the rule, candidate, independent raw-only audit, synthetic cases, control set, and exact container image digest. Run the candidate once, then the auditor once, inside a Docker container. The finite domain is all `3^3 × 3^3 = 729` progress/exposure sign vectors plus the 12 fixed negative controls. No game, X11, GUI, model, input, network service, or shared live allocation.
- **D:** `PASS_T1_IDENTITY_PRECEDENCE_CONSTRUCTION` iff all 729 decisions match an independently implemented oracle, all controls match their frozen expected dispositions/reasons, all four raw mutation probes are rejected, and frozen source/image identities validate. Otherwise retain `FAIL_AUDIT` or the exact `STOP` without retry.
- **C:** Docker Desktop Linux/amd64 container `python@sha256:afc139a0a640942491ec481ad8dda10f2c5b753f5c969393b12480155fe15a63` (CPython 3.12.3), standard library only, deterministic synthetic records, bind-mounted package with candidate/audit sources hash-pinned and outputs confined to the predeclared new result directory. Bytecode writing is disabled.
- **U:** Verifies implementation and audit concordance for the proposed rule only. No empirical endpoint validity, live MAP01 outcome, input safety, threat exposure, effectiveness, or authorization is inferred. This construction does not amend #5085 or #59.

## Explicit validation and decision order

1. Validate record shape, required fields, scalar types, and every fixture/source/model SHA-256 syntax.
2. Only after syntax passes, compare cross-session fixture/source/model/seed/map/skill identities.
3. Validate schedule, pair matching, completeness/audit, exposure bounds and safety conditions.
4. Compute the paired progress and exposure signs, then the directional oracle.

The malformed-model-hash control intentionally changes one row to a syntactically malformed value, so its precedence is unambiguous. A separate well-formed source hash mismatch control checks the equality gate.

## Frozen paired outcomes

The v1 estimands and directional thresholds are unchanged: three pairs, progress sign `+1` when recovery's `(map_exit, alive_at_horizon, -death_count_gain, kill_count_gain)` is lexicographically greater, exposure sign `-1` when recovery's conservative upper bound is below coast's lower bound, and scoped PASS only with at least 2/3 recovery wins and no losses on both endpoints. Threat absence or no positive useful event holds comparative disposition. Instrumentation, comparative, and safety outcomes remain separate.

No formal/live slot is consumed. A successor result is not a substitute for required live evidence.
