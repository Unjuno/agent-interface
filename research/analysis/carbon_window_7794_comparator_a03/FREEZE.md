# Issue #7794 comparator semantics diagnostic A03

## Question and scope

Does the lexicographically earliest globally feasible assignment used by A02 equal the report's declared canonical-order serial ASAP dispatcher on the frozen A02 cases, and what finite counterexample distinguishes them? This is a finite comparator-semantics diagnostic only. It does not rerun A02, compare emissions, or establish a realistic workload effect.

## H / T / D / C / U

- **H:** The two comparator definitions differ on at least one frozen case or on a minimal two-job feasibility control.
- **T:** Treat A02 `frozen_cases.json` as immutable input. Compare (1) global enumeration minimizing the start-time tuple in canonical job order, (2) serial ASAP placing each job in canonical order at its earliest feasible start against already placed jobs, and (3) a minimal two-job case where the first job has a later deadline than the second. Apply the same release, deadline, freshness, precedence, and single-machine non-overlap constraints. A separately implemented recursive auditor reconstructs both comparators and all validity checks.
- **D:** `PASS_DIAGNOSTIC_SCOPED` if the auditor independently matches every candidate row and identifies each case where the two comparators differ; a difference proves the A02 prose comparator is not the executed comparator. `NO_DIFFERENCE_SCOPED` if all schedules match. Any disagreement or omitted case is `FAIL_AUDIT`.
- **C:** Serial ASAP is order-sensitive and may dead-end despite a globally feasible schedule; that may make it a poor baseline, but does not make global tuple minimization equivalent to it.
- **U:** Only the A02 finite synthetic cases and one authored discriminator. No operational schedule, emissions, meter, forecast, GUI, or runtime result follows.

## Freeze

- Base: current `main` at `b673c9f1ca9717cbaeec44aa9feb262a28b9097f`.
- A02 comparator source: PR #7968 head `338e6e8facf1dbdc94c7e3f0c41743945cadf4de`; frozen input: the exact A02 `frozen_cases.json` copied unchanged as `a02_frozen_cases.json`.
- Candidate and auditor use only Python standard library. No model, GUI, network, live task, scheduler policy, or external effect.
- Candidate and auditor each run once, in that order, after this freeze commit. No retries.
- Formal outputs are `formal_a03/candidate.json` and `formal_a03/audit.json`.

Source/input digests are recorded in `SHA256SUMS` before execution. The output manifest is added after both one-shot invocations; frozen source and input bytes remain unchanged.
