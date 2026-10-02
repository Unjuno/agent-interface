# Frozen T1 protocol

Allocation `5593-MULTISTATE-FROZEN-ROSTER-T1-20261002-02`. `FREEZE.json` binds current main, pinned image, exact fixture, independent six-ID roster, candidate, auditor and construction-test digests. Formal outputs are absent at freeze.

## H/T/D/C/U

- **H:** An independent immutable launch roster prevents a candidate/auditor pair from silently agreeing on a truncated episode denominator while preserving the nonterminal SAFE_STOP→RECOVERING state path.
- **T:** Candidate consumes only the six-episode fixture and executes once in a fresh bounded offline container. After candidate exit 0, a separate raw-only auditor consumes fixture + separately frozen roster + candidate output, checks identity/clock/state paths and six corruption controls, and writes its result once. No retries.
- **D:** `PASS_METHOD_MULTISTATE_ROSTER_SCOPED` iff fixture IDs exactly match the frozen unique six-ID roster, every occupancy row sums to six, candidate output exactly matches independent reconstruction, repeated recovery and terminal/censor states remain distinct, and all six frozen mutations are rejected.
- **C:** For real evaluation ledgers, direct all-episode tables may be clearer than transition summaries; the authored finite fixture has no sampling uncertainty.
- **U:** No real cohort, causal effect, independent censoring, model/runtime/GUI result, or production-safety claim. T0-01 remains `METHOD_FAIL_AUDIT` and unchanged.

## Container boundary

Pinned local image ID in `FREEZE.json`; network none, 1 CPU, 256 MiB, 64 PIDs, read-only source and input mounts; candidate and auditor in separate fresh containers. The unrelated already-running container is not entered or modified.
