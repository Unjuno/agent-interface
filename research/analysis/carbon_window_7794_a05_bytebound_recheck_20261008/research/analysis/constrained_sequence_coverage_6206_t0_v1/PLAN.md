# Constrained event-sequence coverage T0

Allocation: `CONSTRAINED-ORDER-COVERAGE-6206-T0-20261002-01`  
Issue: [#6206](https://github.com/Unjuno/agent-interface/issues/6206)  
Branch: `research/6206-constrained-sequence-coverage-t0-20261002`  
Frozen main: `3d33fe482ad55e99943f2c7b40e92c685c3bf92a`

## H / T / D / C / U

**H.** A direct ordered-adjacent-pair suite generated from the independent feasible-trace oracle will catch a planted `REV→ACT` stale-lease admission mutant that a static event-presence covering baseline misses, using fewer traces than exhaustive legal enumeration. A separate ordered-triple suite should catch an `OBS→REV→ACT`-only stale-permit mutant.

**T.** A deterministic standard-library simulator uses the six typed events `ACT`, `OBS`, `REV`, `REL`, `STALE`, `PING`, with fresh reset `(lease open, evidence fresh, no held input)`. `ACT` commits only if lease and evidence are current and no hold is active. `OBS` refreshes evidence but cannot reopen a lease. `REV` closes the lease and releases a held input. `STALE` invalidates evidence and releases a held input. `REL` is a release receipt that is feasible only while a committed hold remains active. `PING` is semantically inert. Enumerate all words of length 0–4; classify infeasible words independently. For every feasible adjacent pair, select the shortest then lexicographically first legal witness trace, excluding the exact `OBS→REV→ACT` triple-control pattern; if any pair lacks a witness, stop pre-candidate. Compare (1) all feasible event-presence subsets in frozen canonical order (a stronger-than-pairwise static baseline, but order-blind), (2) a seed-6206 random schedule sample exactly the size of the ordered-pair suite, (3) the per-pair shortest-witness suite, (4) every feasible length-3 word, and (5) exhaustive feasible length-0..4 schedules. Report adjacent pairs separately from relative-order subsequences. Candidate runs once; separately authored auditor once; retries 0.

**D.** `PASS_METHOD` only if an independent raw-only implementation agrees on every feasible schedule and denominator; all feasible adjacent pairs are covered by the frozen shortest-witness rule; the pair suite detects the `REV→ACT` mutant while the static baseline misses it; `REL` without a live hold is excluded; `PING` preserves semantic state/output; the length-3 suite detects the `OBS→REV→ACT` mutant while the pair suite does not; and the pair suite is strictly smaller than exhaustive legal enumeration. Any disagreement, missing coverage, or safety/release invariant violation is FAIL/HOLD.

**C.** A global pause or exhaustive enumeration may be simpler and stronger at this small scale; the experiment measures only suite size and seeded-fault sensitivity, not runtime value in production.

**U.** This synthetic event reducer does not model payloads, timing, concurrency, hidden GUI state, an actual runtime, task effects, or user input. Legal orders are exactly those admitted by the frozen finite producer/hold rule; no t-way result establishes real GUI reliability.
