# Issue 5407 T2b freeze: capacity-aware reallocation construction

Allocation: `issue5407-market-t2-capacity-reallocation-20261001-02`
Base: `c3227bccfbb7f95ff950edb0d86888ed26f99ece`
Branch: `research/5407-capacity-aware-reallocation-t2b-20261001`

This is a fresh successor to the immutable pre-run STOP for Allocation 01. No runner/auditor ran and no raw artifact was created under Allocation 01.

## H / T / D / C / U

**H.** In heterogeneous workloads where safe executor/verifier pairs are scarce, scarcity-first constrained tuple allocation will reduce safely unserved task value relative to value-first constrained allocation, while preserving zero inadmissible admissions. It may spend more cost or leave low-value work unserved; the oracle is an upper-bound comparator, not an implementable result.

**T.** Freeze a deterministic simulator with 50 seeds, 8 tasks and 10 single-capacity agents per seed. A task needs one capable executor and a distinct-failure-domain verifier meeting its authority and evidence predicates. Compare: (A) unconstrained scalar-cheapest pair selection; (B) constrained value-first greedy assignment; (C) constrained fewest-feasible-pairs-first assignment with value/cost tie-break; (O) exact maximum-safe-value assignment by exhaustive dynamic programming over the 10-agent mask. All policies receive identical workloads, bids, costs and predicates. Emit every decision and final state as JSONL; a separate auditor independently reconstructs feasibility, capacity use, unsafe admissions, safe shortfall, selected cost and oracle value.

Host construction command: `python work/5407_market_t2.py --seed-start 0 --seed-count 50 --tasks 8 --agents 10 --out work/5407_market_t2.jsonl`. Audit command: `python work/5407_market_t2_audit.py work/5407_market_t2.jsonl`. The planned network-disabled CPU-container reproduction is a separate rung and is not claimed or authorized by this freeze.

**D.** Scoped PASS requires (1) A may exhibit unsafe choices, while B/C/O have zero unsafe admissions; (2) C's aggregate safe shortfall value is strictly below B's over the frozen 50-seed matrix; (3) C's total selected cost is at most 125% of B's where B selected nonzero work; (4) O never has lower safe value than B or C; and (5) the independent audit reports zero errors and rejects both registered corruption controls (unsafe-admission mutation and reused-agent capacity mutation). Any invariant violation is FAIL. Missing source/resource/raw identity or incomplete audit is STOP. If the comparative criteria do not separate B and C, retain the measured null result rather than tune the policy.

**C.** This is a deterministic synthetic finite simulator. Scarcity-first allocation may trade aggregate priority value for feasible coverage. A two-agent pair is only a proxy for evidence diversity; the independent failure-domain label is supplied by the generator.

**U.** The workload omits deadlines, task DAG dependencies, strategic bid inflation, non-stationary costs, false evidence claims, and real agent behavior. The result cannot establish truthful bidding, real-world fairness, runtime integration, GUI safety, or product benefit. The 50-seed matrix is fixed and no post-result tuning or rerun is allowed.

## Execution disposition

This is a host-side construction rung because no exclusive Docker/OrbStack CPU window is assigned to this allocation. No GPU, network, model, GUI, or input action is part of the host run. Preserve a container STOP or defer formal reproduction until a separate exact lane is granted; do not infer permission from the separate #5156 release.
