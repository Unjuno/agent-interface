# Issue #7748 T0 — result

**Disposition: `PASS_METHOD_SCOPED` on six synthetic fixtures.** The interval-demand classification agreed with an independently implemented exhaustive preemptive scheduler for every eligible control-only and all-job workload. The deliberate best-effort-first policy missed control job `c0` on a trace both oracles classified feasible. A separate trace had feasible controls but infeasible combined demand with witness `[0,3)`, demand 4, capacity 3. Non-preemptive work returned `UNKNOWN_MODEL_MISMATCH`; missing execution cost returned `HOLD_NO_SCHEDULABILITY_INPUTS`.

## H/T/D/C/U

**H.** For the frozen integer-time, preemptive, unit-speed uniprocessor traces, interval demand agrees with exact exhaustive schedule feasibility and separates model infeasibility from a poor policy's deadline miss.

**T.** [`FREEZE.json`](FREEZE.json) and the SHA-pinned [`cases.json`](cases.json) declare six small cases spanning the policy-miss, control-only/joint feasibility, exact-boundary, out-of-model, and missing-input conditions. Construction tests ran before the one-shot formal candidate; [`run_formal.py`](run_formal.py) invoked candidate and independent auditor once each on local macOS CPython 3.14.5. This tiny exact CPU calculation did not require OrbStack, a live allocation, model, GUI, GPU, host scheduler, or user data.

**D.** `PASS_METHOD_SCOPED`: six input cases, eight eligible control-only/all-job scope checks across four eligible fixtures, zero independent replay errors; all six preregistered input/result/policy mutations rejected by construction tests. Non-preemptive and unknown-cost cases refuse rather than certify.

**C.** A policy can miss even where a valid schedule exists; other traces can exceed demand irrespective of dispatch policy. The included exact oracle differentiates these cases only in the frozen model.

**U.** This is finite method evidence, not a theorem implementation for arbitrary rational/continuous workloads and not a schedulability guarantee for an operating system, multi-core/device path, lock-blocked work, uncertain execution bounds, or physical key release. No conclusion is made about #7722 because its prior allocation is not re-run or reclassified here; its evidence eligibility remains a separate read-only question.

## Per-case disposition

| Fixture | Control / total demand | Independent schedule | Result |
|---|---|---|---|
| Feasible trace, poor policy | feasible / feasible | feasible | best-effort-first policy misses `c0` |
| Controls feasible, joint workload overloaded | feasible / infeasible | feasible / infeasible | witness `[0,3)`: 4 units demanded, 3 available |
| Control-only overload | infeasible / infeasible | infeasible / infeasible | control witness retained in raw |
| Exact-boundary case | feasible / feasible | feasible / feasible | max excess 0; equality is not overload |
| Non-preemptive job | out of model | not run | `UNKNOWN_MODEL_MISMATCH` |
| Unknown execution | missing | not run | `HOLD_NO_SCHEDULABILITY_INPUTS` |

Candidate and auditor were each invoked once; both exited 0 with empty stderr. Receipts bind source hashes and raw/audit output hashes in `formal_01/`. Construction suite: 3/3 passed, including six frozen mutation controls. Reproduce with `python3 -B run_formal.py` only in a fresh copy of this package; the retained `formal_01/` already exists and the runner intentionally refuses to overwrite it. Verify package sums with `shasum -a 256 -c SHA256SUMS`.
