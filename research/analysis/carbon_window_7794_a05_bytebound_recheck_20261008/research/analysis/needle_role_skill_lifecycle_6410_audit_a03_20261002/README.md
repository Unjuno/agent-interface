# Issue #6410 — audit-only allocation 03

Status: **PREPARED / UNASSIGNED; no formal invocation.** This additive successor will independently audit only the immutable candidate raw from allocation 01. It will not rerun the candidate, model, optimizer, training, or timing workload.

## H / T / D / C / U

The scientific H/T/D/C/U remains exactly the reload-vs-reuse lifecycle question in [Issue #6410](https://github.com/Unjuno/agent-interface/issues/6410); this audit-only allocation does not change its hypothesis or thresholds.

- **H:** Loading/validating the retained role-skill package once and reusing its role models preserves every output and lowers lifetime CPU time against per-request reload for the frozen schedule.
- **T:** One separately frozen, raw-only independent audit of the existing 15-block/30,000-row candidate output in the cached WSLc Python image; candidate invocations 0, auditor at most 1, retries 0.
- **D:** Apply Issue #6410's preregistered reconstruction and amortization gates unchanged. A clean audit that misses the thresholds is HOLD; prediction disagreement is FAIL; any provenance, path, or runtime defect is STOP.
- **C:** The retained synthetic seed-3788 package, authored expected output, one WSLc host/image and timing samples. No new timing is measured.
- **U:** This can adjudicate only the retained synthetic run; it cannot establish broad learned-skill benefit, GPU/training performance, GUI effectiveness, or a general runtime claim.

## Predecessor preservation

Allocation 02 remains terminal `STOP_AUDIT_ENVIRONMENT_PATH` (candidate 0, auditor 1, retries 0; no report). Its raw, command history and STOP remain unchanged. Allocation 03 has a fresh allocation identity and output path. The container command performs an in-container `test -f` preflight on every mounted input before executing the auditor, so the prior extra `research/` path prefix cannot silently recur. A preflight failure is still the single terminal invocation; no retry.

## Inputs and limits

The freeze binds the original candidate raw, T0 freeze, scorer/validator bytes and both input digests. Source and evidence mounts are read-only; only `results/audit-03/` is writable. Pinned cached WSLc image, offline network, CPU-only, no GPU. Requested memory is not claimed as enforced; preserve any cgroup/swap warning.

The package is not a scientific result. It may run only after exact-main/source/output checks and an explicit bounded CPU/WSLc assignment plus owner-release confirmation are recorded.