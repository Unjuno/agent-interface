# Issue #5352 — literal hysteresis audit, formal-03

## Disposition

`STOP_AUDIT_SEMANTIC_MISMATCH`. Candidate and independent auditor both traversed 299,592 traces, but implement different transition semantics after `UNKNOWN`. Their counters are retained separately and are not a passing cross-check. This does not reproduce the recovery-gain T6/T7 claim; its source and exact gate remain absent from main and the Issue comments.

## H/T/D/C/U

- **H:** The written no-rebootstrap interpretation and the retained simulator's transition priority may disagree after UNKNOWN; a later high-risk row may leave UNKNOWN under one interpretation but not the other.
- **T:** One frozen candidate enumeration and one separate independently implemented audit over every length-1..6 trace from `{0.64, 0.65, 0.66, 0.69, 0.70, 0.71, STALE, CRITICAL}`.
- **D:** Both count 299,592 traces. Candidate reports 0 critical same-row failures and 101,952 first-valid-after-stale cases still UNKNOWN. Independent audit reports 219,345 critical events, all same-row escalated; 169,434 traces with stale then numeric, 152,928 first-valid cases still UNKNOWN, and 347,220 later valid rows still UNKNOWN. Its first recovery divergence is `(STALE, CRITICAL, 0.64)`, states `[UNKNOWN, ESCALATED, LOCAL]`. The audit currently treats UNKNOWN as sticky across numeric rows, while the candidate checks a fresh high-risk threshold before its UNKNOWN branch. No agreement PASS is assigned.
- **C:** Deterministic exhaustive symbolic traces; Python 3.12 stdlib; Docker Desktop `desktop-linux`; pinned image `python:3.12-slim@sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`; network disabled at build/run; read-only root, all capabilities dropped, no-new-privileges, pids 64, 256 MiB, 1 CPU. Candidate and auditor were separate invocations; auditor imported no candidate code.
- **U:** No calibrated probabilities, task truth, runtime persistence, planner latency/cost, or useful switching benefit. No inference about real runtime safety.

## Stop and recovery history

See `ATTEMPT_HISTORY.md`. It retains the missing `/work` source launch, rejected Windows bind mount, early-stopping diagnostic, initial incompatible summary definitions, and final frozen semantic mismatch without relabeling or retrying formal-03.

## Provenance

`FREEZE-03.json` records the frozen source identities. Formal output is in `results/formal-03/`. `PACKAGE_SHA256.json` covers all package files except itself. The prior #5352 T0 and recovery-gain records are untouched.

## Contract needed for a successor

Define whether numeric risk `>= 0.70` after UNKNOWN may leave UNKNOWN, or whether recovery requires a distinct freshness/revalidation event. Also define whether CRITICAL changes only planner mode or re-establishes evidence freshness. Any successor must have a new allocation ID and freeze this contract before execution.
