# #3270 scorer replay CI addendum

Status: **PASS_REPLAY_CI_GATE / FORMAL MAP01 ALLOCATION STILL FAIL**

Evidence integration base: `30d98dcf65e9d5a1772083b416b84753f28f0b4e`  
Date: 2026-09-30

## H / T / D / C / U

- **H:** The bounded replay gate that reconstructs scorer missed-period accounting is executable through the repaired repository CI checkout path.
- **T:** Inspect both isolated replay workflow runs after completion. They execute the deterministic replay gate; neither runs ViZDoom nor consumes a MAP01 allocation.
- **D:** **PASS for replay CI only.** Run 35471857847 (PR event, tested head `b859221b9ae3bbb790c434d82a99ba6f713b8f81`) and run 35471911447 (workflow_dispatch, tested head `d287443c74b274e934c711cde262aaee8822c8ed`) both completed with conclusion `success`. Each job's container setup, shallow checkout, replay gate, and cleanup steps concluded `success`. Neither run uploaded an artifact. Earlier local Docker/Obstac replay and scheduler-boundary replay remain distinct evidence recorded in #3270.
- **C:** This verifies CI replay plumbing and the deterministic accounting gate only. It does not alter allocation -07's retained preregistered `FAIL` (pair-02 COAST_CONTROL had one missed sample period), and establishes neither recovery efficacy nor a MAP01 clear.
- **U:** No fresh MAP01 allocation was run by these checks. Any formal follow-up still needs its own current-main source freeze, exact allocation/lease, collision check, first-outcome retention, and independent audit.

## Provenance

- Parent issue: [#3270](https://github.com/Unjuno/agent-interface/issues/3270)
- Existing replay report, retained unchanged: [SCORER_JITTER_REPLAY_3270.md](SCORER_JITTER_REPLAY_3270.md)
- CI workflow runs: [35471857847](https://github.com/Unjuno/agent-interface/actions/runs/35471857847), [35471911447](https://github.com/Unjuno/agent-interface/actions/runs/35471911447)
- Repaired workflow PR: [#3288](https://github.com/Unjuno/agent-interface/pull/3288)

This additive status clarification does not edit prior reports, raw artifacts, allocation outputs, or dispositions.
