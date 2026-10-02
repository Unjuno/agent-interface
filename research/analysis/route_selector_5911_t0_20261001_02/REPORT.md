# Issue #5911 T0 — explicit route selector and topology check

**Result: `PASS_METHOD_SCOPED` (finite synthetic selector contract only).**

## H / T / D / C / U

**H.** An explicit route selector, cost table, and set-valued tie rule distinguish a true route change from a cost change on an unchanged route.

**T.** Five frozen interventions were evaluated once: predecessor +80 ms, predecessor half-model cost, a true route switch, an unchanged exact tie, and a tie broken by intervention. The candidate reads each explicit route-cost table and compares pre/post minimum-cost route-ID sets. The independent auditor recomputes route costs and argmin sets from the frozen fixture, then checks three corruption controls.

**D.** All five rows reconciled. Predecessor +80 ms remained model_path (130→210 ms) versus alternate 260 ms; status FIXED_TOPOLOGY, endpoint delta −80 ms. Half-model remained model_path (130→80 ms) versus 260; delta +50 ms. True route change selected alternate and returned NONSTATIONARY_INTERVENTION/no numeric delta. Preserved tie kept {route_a,route_b} at 100→120 ms and returned FIXED_TOPOLOGY/delta −20 ms. Broken tie changed {route_a,route_b} to {route_b}, returned NONSTATIONARY_INTERVENTION/no numeric delta. Independent audit errors=[]; 3/3 corruption controls rejected. Outcome PASS_METHOD_SCOPED.

**C.** Minimum total cost is normative only within these fixtures. A predecessor “alternate endpoint” may not have been intended as a competing route; the new synthetic contract does not resolve external semantics. A fixed-topology sensitivity analysis may need a different selector such as maximum path duration.

**U.** This establishes only the finite selector/tie contract on five hand-built cases. No real trace, performance, GUI, agent choice, causal optimization, safety, GPU, container, MAP01, or Issue #59 live-control claim.

## Reproducibility

Allocation `ROUTE-SELECTOR-5911-T0-20261001-02`; frozen main `906198f2b7b72db7d359921b50d9b6a22f503548`. Candidate ran once and independent auditor once in the Codex V8 runtime using the recorded binding adapter. Original #5851 sources/results were read-only. Two pre-execution loader/binding errors produced no candidate function or output; they are retained in `STARTUP_ATTEMPTS.json`. No retry after a candidate run.

Frozen Git blob identities: fixture `f1296f78ef1030361c5ccb64c8df6fb0965cb4c8`; candidate `5878288771eb485580211aacd3ae040d58eab58c`; auditor `20df8f47309a50ff9bbd3bc370f25be5b77bf1d2`. Raw candidate and audit are retained beside this report.
