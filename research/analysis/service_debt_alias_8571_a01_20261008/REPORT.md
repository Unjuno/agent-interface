# Issue #8571 A01 — service-debt representation invariance

Disposition: `PASS_METHOD_SCOPED`. Full result and frozen allocation inputs
are preserved in `FORMAL_RESULT.md` and `FREEZE.json`.

## Construction log (pre-freeze)

The initial construction test incorrectly required every nontrivial partition to
increase A's share. It failed: the frozen tie rotation gives no share increase
in `alias_p02_k2a`, `alias_p03_k2b`, `alias_p04_k2c`, and `alias_p05_k2d`.
Inspection of all 14 fixed partitions found 10 with increased A units and these four nulls. This was a
construction failure, not a formal run. The preregistered discriminator was
narrowed before freezing to existential evidence across the complete fixed set;
no partition is removed or selected post hoc. The initial revoked-control
assertion also treated explicit zero-service A as absent; it now asserts A=0,
B=4, and retains the exclusion record.

## H / T / D / C / U

- **H:** On the frozen finite shared-resource trace, the #6613 least-cumulative-service comparator keyed by caller-presented identity can be advantaged by splitting one principal's queue across aliases. Grouping by an independently supplied fixture parent should remove that alias advantage without merging genuinely distinct principals or changing hard eligibility. Splitting equal total service into smaller same-principal jobs is a separate negative/diagnostic stratum; it is not assumed to be semantically neutral in real GUI work.
- **T:** Exact, deterministic CPU model; two principals, one serial resource, four one-tick service opportunities, eight same-priority requests all available at time zero. Enumerate all 15 set partitions of four A requests (Bell number B4): one caller, every 2-block partition, every 3-block partition, and four aliases. Compare FIFO, least cumulative service keyed by presented caller, and the same debt rule keyed by fixture-trusted parent. Add equal-total-service fragmentation, three honestly distinct principals, revoked work, missing joint grant, a deliberately false parent claim, and a mandatory release. The candidate emits attempts only. A separately implemented raw-only auditor joins a frozen outcome oracle and checks every row, policy choice, exclusion, release, wait and effect credit. No randomness or inference.
- **D:** `PASS_METHOD_SCOPED` only if the independent replay is exact; at least one of the 14 fixed nontrivial A alias partitions increases A's four-slot consideration share under caller-keyed debt versus the one-caller control; trusted-parent debt reproduces the one-caller allocation for every partition; fragmentation does not change the four-slot service-unit allocation in its matched fixture; genuinely distinct principals remain separate; denied/revoked requests are never dispatched; the release occurs at its frozen time before any later optional dispatch; and all frozen audit mutations are rejected. All 14 partition outcomes, including nulls, remain in the report. Any safety/accounting mismatch is `FAIL_METHOD`; absent the alias discriminator is `FAIL_NO_ALIAS_ADVANTAGE_IN_FIXTURE`. These labels apply only to this authored trace.
- **C:** FIFO is invariant to caller labels and may be preferable when arrival order is the legitimate right. Atomic job size, deadlines, semantic value, workload infeasibility, real identity provenance, or an already-authoritative queue policy may dominate the model. A trusted parent map is assumed input here, not implemented authentication.
- **U:** No real users, aliases, GUI, consent, identity collection, authority path, live scheduler, or production fairness are tested. Equal service units do not establish equal semantic value. This does not transfer Moulin's queueing impossibility theorem to GUI scheduling and does not recommend collecting identity data.

## Prior evidence and scope

This is a new additive successor to #6613's representation-manipulation gap, not a retry of its preserved `STOP_PREREGISTRATION_HASH_MISMATCH` or its later service-debt `FAIL_HYPOTHESIS`. The earlier #6613 A01 found no wait improvement for its own 32-seed, variable-service comparison; this A01 tests caller-identity representation, an untested estimand. #6347's repeated-window work concerns delay swaps and boundary gaming, not alias partitions of long-horizon service-debt queues. All predecessor records remain unchanged.

The service-debt rule is operationalized from the retained #6613 A01 candidate (`service_debt_deadline_6613_a01/candidate.py`, blob `04641813e546606236a10a99e935be7739d16c3e`): among eligible requests choose the group with least accumulated service; rotate the tie order; then choose that group's earliest request. This package tests a grouping-key substitution only. It does not claim source identity with, or repeat, the prior randomized allocation.

## Execution contract

Base: `5215aab506f43c8a02470d495b7352b1326a9580`. Runtime selection follows #3352: native Ubuntu WSL is appropriate because the frozen question is a deterministic standard-library CPU simulation with no container boundary. No WSLc allocation, Docker daemon, GPU, network, live GUI, model, or OS input is used. Freeze files and hashes before the one candidate invocation; run the independent auditor exactly once only after candidate success. Outputs are collision-refusing and are never overwritten. A first formal failure is retained, not rerun.

Formal invocations recorded from the frozen allocation (do not rerun):

```bash
python3 -B candidate.py trace_fixture.json candidate_raw.json
python3 -B audit.py trace_fixture.json outcome_oracle.json candidate_raw.json audit.json
```

`candidate_raw.json` contains no outcome-oracle fields. The auditor computes verified useful completions from `outcome_oracle.json` after reconstructing the dispatch trace.

