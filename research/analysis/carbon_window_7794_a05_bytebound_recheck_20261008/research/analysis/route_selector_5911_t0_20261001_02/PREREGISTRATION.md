# Issue #5911 T0 — explicit route selector and topology check

Allocation: `ROUTE-SELECTOR-5911-T0-20261001-02`
Base main: `906198f2b7b72db7d359921b50d9b6a22f503548`
Branch/path: `research/route-selector-5911-t0-20261001-02` / `research/analysis/route_selector_5911_t0_20261001_02/`
Execution: deterministic JavaScript in the Codex analysis runtime; no host process, GPU, container, model, GUI, or external input.

## H / T / D / C / U

**H.** Explicit minimum-cost route sets and tie semantics eliminate the predecessor fixture's false branch-change label: +80 ms and half-model interventions retain the same selected route; true route change and tie-breaking are detected; an unchanged exact tie remains set-valued and can carry a numeric endpoint delta.

**T.** Freeze `fixture.json`, `candidate.mjs`, `audit.mjs` before execution. Candidate reports before/after route costs, selected argmin route-ID sets, topology status, and numeric delta only when selected sets are identical. Independent auditor recomputes each route cost and argmin set, then checks corruption controls (status, delta, route set). Five cases: predecessor +80, predecessor half-cost, true switch, preserved tie, broken tie.

**D.** `PASS_METHOD_SCOPED` iff all 5 rows match independently recomputed costs and route sets; numeric delta exists exactly when selected sets stay identical; true route switch and tie break return `NONSTATIONARY_INTERVENTION`; 3/3 corruptions reject. Otherwise retain FAIL with exact errors. No tie is resolved by arbitrary list order.

**C.** Minimum total cost is explicit for this fixture; alternate routes may be descriptive in predecessor and not actual options. This synthetic selector may not represent critical-path maximum or agent task choice.

**U.** Finite construction method only. No real causal trace, GUI, performance, safety, runtime, GPU, MAP01, or optimizer claim. This cannot satisfy #59.

This allocation 02 replaces the v1 preparation-only freeze after main advanced before candidate start. Allocation 01 has candidate/auditor=0/0 and no scientific result.