# Opportunity-conditioned age of actuated information — T0

## H / T / D / C / U

**H.** Observation-delivery AoI and completed-cycle latency can rank two routes identically or favor a route that has worse observation-generation-to-relevant-effect age and more missed opportunities. A lineage-aware card should detect the inversion without crediting irrelevant motor activity or receipt-only events.

**T.** Freeze eight synthetic opportunities/cycles specified in `FIXTURE.json`: fresh observation then stalled effect; older still-valid observation with timely effect; frequent irrelevant pulses; dispatch without independent effect; expired cue before cycle start; no intervention-needed quiet interval; multi-observation ambiguous ancestry; incomparable clocks. Compare delivery AoI, cycle latency, and lineage/effect card on every row. Candidate emits raw rows once; independently authored auditor reconstructs them once. Mutation controls swap observation/effect identity, remove an effect, and make clocks incomparable. Retries 0.

**D.** `METHOD_PASS_SCOPED` iff all eight cases preserve the declared opportunity denominator and distinctions, detect the planted ranking inversion, keep ambiguous lineage / absent independent effect / incomparable clocks UNKNOWN, do not reset on irrelevant or receipt-only events, and mutation controls are rejected. Else `FAIL_METHOD` or pre-computation `STOP`; no retry.

**C.** Freeze main `6cd70ad4bfad74e11658057bf024918bffb24add`, 2026-10-01 UTC; pure Python 3 stdlib, CPU host. GitHub Issue #5085 assigns the shared Docker CPU lane to another owner (#5074 retains next slot); therefore no Docker/OrbStack query beyond read-only `docker ps`, no container start, no game/model/GUI/input/GPU/network/shared allocation. This is a methods-only synthetic table, not a formal #59 allocation.

**U.** Synthetic method discrimination only. No evidence of live MAP01 timestamp quality, actual model-consumed observation, task effect, controller efficacy, safety, human-tempo benefit, or general GUI validity. T1 needs separate explicit allocation, source-bound lineage, independent scorer, comparable clocks, and preregistered all-opportunity denominator.

## Frozen run gate

Run `python3 -B candidate.py` exactly once, then `python3 -B audit.py` exactly once. Candidate writes `results/t0/RAW.json`; auditor reads raw plus fixture and emits `results/t0/AUDIT.json`. Do not rerun either script after first invocation.
