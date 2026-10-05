# #8152 T0 A01 — frozen design before allocation

Allocation: `UNJUNO-8152-STAT-TRACE-A01-20261005`  
Branch: `research/statistical-trace-reducer-8152-t0-a01-20261005`  
Base: `84be79757c8bc18eea1ecaf5edb8f392e3e6e425`  
Container: `python@sha256:f3fa41d74a768c2fce8016b98c191ae8c1bacd8f1152870a3f9f87d350920b7c` (`linux/arm64`), no network, read-only source, separate writable output, one CPU requested. No claim of a hard memory limit.

## H/T/D/C/U

**H.** In this finite flaky trace fixture, sequentially screened reduction preserves the exact target fingerprint on disjoint held-out seeds while using fewer search replay queries than fixed-repetition reduction. A one-run reducer may accept a causal-event removal after a rare matching fingerprint.

**T.** Run a SHA-256-seeded finite event plant with fixed authority/setup/release invariants, two causally ordered target events, two nuisance events, and a same-exit-code competing fingerprint. Compare (A) one replay per candidate, (B) 80 replays per candidate with exact one-sided Clopper–Pearson noninferiority bounds, and (C) looks at 10/20/40/80 with Bonferroni alpha spending across candidate decisions and looks. Noninferiority margin is 0.25. The final trace is evaluated on 200 separate held-out identifiers with a 3-method familywise bound. Source defines the exact event and fingerprint rules. No real trace, GUI, model, user data, network, or external action is used.

**D.** Auditor must independently reconstruct every row, final trace, bound, query count, and confirmation. PASS_METHOD_SCOPED requires no accepted unsafe trace, exact-fingerprint distinction from the same-exit-code competing event, no search/confirmation seed overlap, all hostile controls rejected, held-out noninferiority for C, and fewer C than B search queries without weaker hard invariants. Otherwise preserve FAIL/HOLD; no candidate/auditor retry or post-result tuning.

**C.** Fixed repetition may be more reliable; the fixture may favor its authored rates/order; conservative bounds may consume the full budget; deterministic replay with source-bound reset could be simpler.

**U.** The hash-derived finite fixture is not a retained GUI failure or an empirical distribution. Exact confidence calculations are conditional on independent Bernoulli sampling as modeled; the test does not establish real-world calibration, stationarity, causal root cause, minimality, safety, or deployment utility. Statistical outcomes only govern optional trace reductions; authority and cleanup are deterministic hard constraints.

## Invocation boundary

Construction tests are not formal allocations. After source freeze and Issue preregistration, invoke the candidate once, then invoke the raw-only auditor once if candidate exits 0. No retries. Any launch failure consumes the allocation and is retained as infrastructure STOP. Both roles get read-only source and separate output mounts; auditor sees protocol and raw candidate only, not candidate code.
