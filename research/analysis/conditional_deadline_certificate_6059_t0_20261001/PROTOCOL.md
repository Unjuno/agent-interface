# T0 protocol — Issue #6059

Allocation: `ROUTE-DEADLINE-6059-T0-20261001-01`  
Intended base: `9371fda8617bdf49e7fbeebb04fa64a633712aaa`  
Scope: abstract integer ticks; finite deterministic cases; no GUI, model, application, network, live agent, or product claim.

## H / T / D / C / U

- **H:** A conservative route certificate can identify bounded routes whose worst-case typed-terminal time is within deadline; upper-bound failure alone remains UNKNOWN; IMPOSSIBLE requires an independently justified strict lower bound.
- **T:** Nine frozen scenarios; a pure candidate emits labels once. A separately implemented exhaustive simulator checks all finite service assignments and certificate soundness once. The burst fixture has two serial FIFO queues and two simultaneous jobs; the target completion is `A1 + max(B1, A2) + B2`.
- **D:** `PASS_METHOD_SCOPED` if all nine declared labels match the exact oracle, every MET is on-time on every enumerated trace, every IMPOSSIBLE misses on every trace and has an independent strict lower bound, and all unsupported/mismatched cases remain UNKNOWN. Otherwise `FAIL_UNSOUND_CERTIFICATE` or `HOLD` if execution/artifact integrity fails.
- **C:** The sufficient path bound can be pessimistic, and finite fixtures do not cover arbitrary queue disciplines, retries, branching, scheduler interference, clock drift, or semantic completion.
- **U:** No real route has been shown to possess these deterministic service guarantees. Timely typed termination is not useful task success. This method cannot supply a production deadline, latency, safety, or performance claim.

## Formal run rule

Run `candidate.py` once on `scenarios.json`, then `audit.py` once over the exact candidate bytes and the same frozen input. Do not patch or rerun after seeing formal output. Construction tests are pre-freeze and non-formal. Preserve stdout/stderr, exit codes, timestamps, input/output SHA-256, and the full audit. Docker Desktop is installed, but `docker info` did not return within the bounded probe and the shared container slot is reserved elsewhere; this allocation is host-only Python stdlib.
