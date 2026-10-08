# #5694 A04 — matched-capture phase contrast

## Successor boundary

A03 remains immutable at [PR #6799](https://github.com/Unjuno/agent-interface/pull/6799) with `HOLD_PHASE_CONTRAST_NOT_MATCHED`. A03's hit/miss arms changed their capture schedules and observation horizons. This new allocation tests the same narrow synthetic boundary distinction with those schedule fields matched; it is not an A03 rerun or reinterpretation.

## H / T / D / C / U

- **H:** Under an identical declared capture schedule and horizon, moving a finite cue from just before the first capture to just after that capture yields `eligible_effect` in the hit arm and `not_acquired` in the miss arm.
- **T:** One deterministic standard-library replay with nine rows: eight exogenous opportunities plus one no-opportunity control. The phase pair uses captures `[10, 50]` ms, horizon `60` ms, expiry `20` ms, and onsets `9` versus `11` ms. Other rows cover late delivery, delivered/no decision, decision/no verified effect, safe stop, unsynchronized clocks, and right censoring. Candidate reads only `fixture.json`; scoring-only expectations are in auditor-only `oracle.json`. A separate auditor reconstructs outcomes from source events, checks them against the scoring oracle, and requires the phase capture schedule, horizon, and expiry to match. Five raw mutations are frozen: missing row, duplicate row, wrong phase class, changed schedule, forged effect receipt.
- **D:** `PASS_METHOD_SCOPED` only if all nine rows are present exactly once, the matched phase pair gives the frozen classifications, every row and receipt matches independent audit, all five mutations fail audit, and UNKNOWN/NOT_APPLICABLE controls remain distinct. Any false classification is `FAIL_METHOD`; a protocol/provenance problem is `STOP`. No live-effect claim follows.
- **C:** The synthetic cue, clocks, and event joins are fully specified and may be easier than operational telemetry. A deterministic fixture cannot estimate miss prevalence or causal effect in a live controller.
- **U:** Finite authored fixture only. No GUI, model, input, network, container, GPU/CUDA, live #59 evidence, safety rate, human-tempo, or product claim.

## Frozen allocation and execution

- Issue: #6803; allocation: `EXOGENOUS-OPPORTUNITY-5694-A04-MATCHED-PHASE-20261002-01`.
- Main at intake: `52c42c40bb074f46db1dc74afb20508e68bc1282`.
- Pre-formal main refresh: `c17490cae4cb1e9600b816484f5103e3613700af`. The cumulative compare from intake changed only `.github/workflows/analysis-index.yml`, `RESEARCH.md`, `research/analysis/README.md`, and unrelated #6155/#6645 research evidence. `ROADMAP.md` and `docs/CURRENT_GOAL.md` remain unchanged; no A04 source/data/runtime path overlaps. Candidate, auditor, fixture, oracle, tests, and frozen decision gates are unchanged.
- Owner/runtime: this Codex desktop research task; native Windows AMD64, CPython 3.11.9, standard library only, CPU.
- Branch: `research/exogenous-opportunity-5694-matched-phase-a04-20261002`.
- Package: `research/analysis/exogenous_opportunity_5694_matched_phase_a04_20261002/`.
- Window: 2026-10-02 20:15–20:30 UTC. Candidate process max 1; independent auditor process max 1; retries 0. No WSLc, Docker/OrbStack, GPU, CUDA, network, model, GUI, or external effect.
- Candidate command: `python -B candidate.py --fixture fixture.json --out execution/formal-01/candidate.raw.json`.
- Auditor command: `python -B auditor.py --fixture fixture.json --oracle oracle.json --raw execution/formal-01/candidate.raw.json --out execution/formal-01/audit.json`.
- Exact source, fixture, oracle, test, and command hashes are in `FREEZE.json`. Both output paths must be absent in the final pre-run check. Any failed precondition means STOP and no retry.

Construction tests are not formal candidate/auditor executions. They must pass before source freeze and must not modify any file listed as frozen after `FREEZE.json` is committed.
