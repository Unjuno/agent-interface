# Issue #5797 — safety-constrained portfolio T0

Status: `METHOD_PASS_SCOPED` for a synthetic finite construction only. This is not a benchmark recommendation, route promotion, or estimate of real fault probability.

## H / T / D / C / U

- **H:** On one frozen task/fault matrix with unequal costs, detection-aware selection can expose a safety sentinel omitted by a cheaper capability-coverage-only portfolio, while preserving unknown cells.
- **T:** T0 CPU-only exhaustive enumeration of all 8 subsets of three synthetic tasks. Two cheap tasks share identical ordinary capability labels but detect different faults. A costly release sentinel is deliberately outside the ordinary coverage objective and mandatory by safety policy. One equivalent mutant is excluded, and one fault has no known detector. Candidate and independently authored oracle use separate code paths.
- **D:** Scoped pass requires: coverage-only negative control omits the mandatory release-loss detector; detection-aware output retains every mandatory sentinel and every known-detectable non-equivalent fault; unknown cells remain unknown; equivalent mutant is not counted as an adequacy target; independent enumeration agrees.
- **C:** The toy costs and fault-detection matrix are authored, deterministic, and small. Real fault identity, detection rates, costs, cross-task effects, and benchmark validity are not measured. With these costs, no screening-cost saving exists while retaining every mandatory/known fault; the safety portfolio equals the full suite.
- **U:** Matrix overfitting; stochastic detection; task interactions; cost/queue drift; synthetic mutants' relationship to real faults; selection quality on a held-out cohort.

## Freeze and execution

- Repository base at intake: `b7b724ee06125a146c68071c1d03e9556a70c5f6` (`main`, 2026-10-01T14:03:56+09:00). `origin/main` was verified equal immediately before checkout. No Issue #5797 branch or PR was found at intake.
- Candidate: `candidate.py`; independent oracle: `audit.py`; tests: `test_candidate.py`. Standard library only; Python 3.12.10.
- Executed commands: `python candidate.py`, `python audit.py`, `pytest -q`.
- Docker Desktop was present but daemon/WSL backend was unavailable at experiment time. This rung therefore ran directly on the local host CPU, not in a container. No model, GUI, app, network service, or shared runtime was used.
- All attempt history is retained in `ATTEMPTS.md`; the initial bad matrix and two independent-auditor construction failures are not relabeled or erased.

## Result

- 8/8 subsets were enumerated.
- Cheapest capability-only portfolio: `{cheap_a}`, cost 1; it covers both ordinary labels but misses `release_loss` and `stale_authority`.
- Random same-cost support has two one-task portfolios; both miss `release_loss` (0/2 retain the sentinel).
- Safety/detection-constrained portfolio: all 3 tasks, cost 6; all three mandatory sentinels and all known-detectable non-equivalent faults remain covered.
- `unknown_fault` remains UNKNOWN for all three task rows (3 unknown cells); it is never recorded as a miss or a kill.
- The equivalent mutant is explicitly outside the detection-adequacy target.
- Candidate and independent oracle agree; all 4 local tests pass.

Interpretation: capability labels alone are insufficient in this constructed matrix, but enforcing known fault discrimination eliminates all cost savings. This is exactly a method demonstration; it gives no evidence that portfolio compression is beneficial on repository benchmarks. T1 needs a provenance-backed #12/#5541-compatible retained cohort and independent matrix review.

## Failed construction history

1. Initial candidate matrix put `release` in the ordinary coverage labels; coverage-only then selected the costly sentinel and failed to create the planned negative control. Preserved as `attempt1.raw.json` and `attempt1_test.raw.txt`.
2. First independent-auditor execution stopped on an empty-set union implementation error. Preserved as `audit_attempt1.raw.txt`.
3. Second independent-auditor execution stopped on an inverted assertion for the same-cost negative control. Preserved as `audit_attempt2.raw.txt`.
4. Corrected frozen construction and auditor then ran once to completion; no candidate-scoring result was rerun after a formal/live allocation because this is an unallocated synthetic T0.

## Scope / next gate

This result is not a claim that coverage-only selection is unsafe generally. It proves only that capability coverage does not imply fault discrimination in this explicitly constructed matrix. No task, fault, or cost here came from empirical benchmark data. Do not promote a route or replace the full #12/#57 confirmation cohort. Before any T1: independently verify task/oracle provenance, predeclare costs and fault classes, keep a sealed full matched confirmation cohort, and obtain a collision-free allocation.
