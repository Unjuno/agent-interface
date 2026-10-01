# Issue #5851 T0 — causal critical-path elasticity

Allocation: `CAUSAL-CRITICAL-PATH-ELASTICITY-5851-T0-20261001-01`  
Frozen main: `2fbbd0430359a2de11609372e003c3f6ad632a36`  
Scope: deterministic model-free DAG simulator; no shared Docker/OrbStack, GUI, model, provider, network, user task, or safety-path perturbation.

## H / T / D / C / U

**H.** In overlapping planner/local work, region time share and largest single span misrank at least one end-to-end optimization opportunity. A source-bound causal DAG plus a paired 50% region-cost intervention identifies the endpoint effect on fixed-topology cases, returns `NONSTATIONARY_INTERVENTION` when the intervention changes route topology, and returns `UNKNOWN` when causal edges/clocks are incomplete.

**T.** Freeze six deterministic cases: (1) serial bottleneck; (2) long parallel off-path region; (3) near-tie competing paths; (4) serial critical handoff after a long off-path span; (5) branch-changing region perturbation; (6) missing causal edge/cross-clock uncertainty. For each fixed-topology region, reduce its declared duration to exactly one half and recompute the end-to-end endpoint. Compare this paired finite difference with an independently computed static DAG bound. The branch-changing and incomplete-evidence cases must not emit numeric elasticity estimates.

**D.** `METHOD_PASS_SCOPED` iff an off-path region is selected by at least one span heuristic but yields zero endpoint improvement; all fixed-topology endpoint values and half-cost effects equal an independent exhaustive-path enumerator; the near-tie case captures path switching; branch change is labelled `NONSTATIONARY_INTERVENTION`; missing-edge/clock evidence is `UNKNOWN`; four corrupted-output controls are rejected; candidate and audit each run exactly once.

**C.** The fixture is a tiny deterministic synthetic DAG. No real event stream, endpoint, scheduling noise, cost distribution, or task trajectory is sampled. Nodes and edges are explicit and authoritative only inside the fixture.

**U.** This is a method/construction result only. It does not estimate real critical paths, justify a production optimization, establish MAP01/GUI efficacy, or demonstrate end-to-end speed, task correctness, human tempo, or safety. T1 remains conditional on a retained trace with eligible synchronized causal events, a safe intervention, and a separate allocation.

## Frozen cases and gate

Case identities, node durations, region labels, causal edges, clock domains and route-change rule are fixed in `fixtures.json`. Candidate input/output files must not exist before the sole candidate invocation. The independent auditor uses path enumeration rather than the candidate's dynamic-programming implementation. Preserve all raw output and hashes; no rerun, tuning, or substitute dataset after invocation.
