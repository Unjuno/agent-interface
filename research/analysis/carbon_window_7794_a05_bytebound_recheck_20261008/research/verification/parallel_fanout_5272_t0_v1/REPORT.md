# T0 result — Issue #5272 parallel verifier fan-out

**Disposition: `PASS_SYNTHETIC_T0`, narrowly scoped to the frozen logical-time
model.** The preregistered primary endpoint passed and the independent audit
found no violations. This is not evidence of wall-clock latency improvement in
real verifiers, an integrated runtime benefit, or task success.

## Primary result

| Workload / policy | Decision-ready logical time | Typed decision | Peak workers |
|---|---:|---|---:|
| Independent / serial | 19 ms | PASS | 1 |
| Independent / fan-out | 8 ms | PASS | 3 |
| Dependency chain / serial | 13 ms | PASS | 1 |
| Dependency chain / fan-out | 13 ms | PASS | 1 |
| Contention control / serial | 12 ms | PASS | 1 |
| Contention control / fan-out | 12 ms | PASS | 3 |

Independent checks improved by 11 logical ms (57.9%), meeting the frozen gate
of at least 25% (`8 * 4 <= 19 * 3`). The dependency chain has no available
parallelism. Under the frozen slowdown model the contention control erases
the nominal fan-out gain completely.

## Full outcome matrix

| Workload | Serial → fan-out decision-ready ms | Result preserved? | Notes |
|---|---:|---|---|
| Independent | 19 → 8 | Yes: PASS | Primary endpoint passes. |
| Dependency chain | 13 → 13 | Yes: PASS | Dependency order limits concurrency to one. |
| Timeout | 7 → 4 | Yes: UNCERTAIN | Timeout does not become PASS. |
| Verifier UNKNOWN | 10 → 6 | Yes: UNCERTAIN | UNKNOWN remains unresolved. |
| Optional deadline | 9 → 9 | Yes: PASS | Optional checks do not delay mandatory decision. |
| Mandatory deadline | 7 → 7 | Yes: UNCERTAIN | Missing mandatory result never becomes PASS. |
| Budget saturation | 4 → 4 | Yes: UNCERTAIN | Budget limits hold; optional work can consume reserved budget under fan-out. |
| Decisive FAIL | 2 → 2 | Yes: FAIL | Remaining jobs are cancelled. Fan-out reserved 13 cost units versus 2 serial units before the FAIL; parallel speculation is measurably wasteful here. |
| Contention control | 12 → 12 | Yes: PASS | Frozen service slowdown nullifies latency gain. |

All 18 case/policy rows matched their frozen typed decisions. Mandatory PASS
rows contain only completed PASS evidence; deadlines, UNKNOWN, and budget
shortfall remain fail-closed. Worker caps and cost-unit budgets were respected.
The raw-only auditor independently recomputed the matrix and result digests,
returned zero errors, and rejected all six deliberate corruption controls.

## H/T/D/C/U conclusion

- **H:** supported only for the independent synthetic workload under the
  specified fixed costs and three-worker cap; not a general fan-out result.
- **T:** nine deterministic workloads × two policies; one formal run and one
  separate independent audit, with exact inputs and sources pinned in
  [`FREEZE.md`](FREEZE.md).
- **D:** all frozen finite-model gates passed. The outcome is
  `PASS_SYNTHETIC_T0`; the parent Issue #5272 remains open.
- **C:** logical milliseconds are simulated, not measured. Real CPU/GPU/RAM,
  service-time distributions, scheduling noise, rate limits, cancellation
  latency, cleanup, hidden dependency/correlation, and task-level quality were
  not measured. Decisive FAIL shows a substantial reserved-work penalty under
  fan-out.
- **U:** whether real verifier workloads preserve the gain; whether bounded
  cancellation and cleanup work in a real process boundary; and how adaptive
  worker count changes the latency/resource frontier remain unknown.

## Evidence and integration boundary

- Formal raw: [`out/formal03/raw.json`](out/formal03/raw.json), SHA-256
  `5d2914f3eb1a2d2b9fd8fb1fbefd391a6832a136f024d43cb4d30dc4aa2fcddf`.
- Independent audit: [`audit.json`](audit.json), zero errors, six of six
  corruption controls rejected.
- Exact source/input freeze: [`FREEZE.md`](FREEZE.md).
- Exact commands and invocation counts: [`RUN_LOG.md`](RUN_LOG.md).

This artifact does not close #5272. A next rung should use fixed, same-plan
verifier processes with measured CPU/RAM/service distributions, real bounded
cancellation and cleanup witnesses, and a preregistered useful-evidence versus
speculative-work budget. Keep the contention and decisive-FAIL penalties as
required controls. Any such run needs a new allocation and immutable evidence.
