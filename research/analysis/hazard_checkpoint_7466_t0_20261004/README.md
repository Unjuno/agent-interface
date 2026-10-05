# Issue #7466 — exploratory T0 construction

Status: **exploratory simulator probe; not a formal efficacy result**.

## H / T / D / C / U

- **H:** A visible, predictive interruption-risk signal can make cost-sensitive checkpoint timing cheaper than fixed or event-boundary timing; with no informative signal the policy should abstain and match its event-boundary fallback.
- **T:** Deterministic standard-library simulation only. 400 paired seeds per cell; 80 ticks; checkpoint cost 3 cost-units; policies are fixed every 10 ticks, event every 5 ticks, and adaptive at a visible high-risk window (or event fallback when no signal). Informative cohort uses a perfectly predictive visible periodic signal (hazard .25 in its four-tick window, .01 otherwise); uninformative cohort has stationary hazard .05 and no signal. Total cost is lost work plus checkpoint count × 3. No task/GUI/OS/provider mutation.
- **D:** Construction probe only. Report per-cell mean/median and paired raw rows. The adaptation hypothesis is not promoted unless a more realistic frozen study passes held-out predictive calibration and cost/correctness gates in #7466. The uninformative cohort must exactly match fallback for all seeds.
- **C:** The perfect signal and hand-set hazards intentionally make the informative cohort easy; the exposure lookahead (16 ticks) and costs are arbitrary. Per-tick effects, checkpoint serialization/verification time, task semantics, non-idempotent replay, clustered distribution shift, Brier calibration, and sensitivity are not modeled. Candidate and evaluation use the same deterministic schedule family.
- **U:** No real interruption distribution, calibrated predictor, agent runtime, safety/resume correctness, user benefit, or production checkpoint policy is established. This is only a simulator construction discriminator.

## Execution and audit

Run from this directory with `python3 sim.py .`, then `python3 audit.py raw.jsonl`.
`raw.jsonl` contains all 2,400 per-seed rows and `summary.json` contains the cell aggregates. The independent audit reconstructs row uniqueness, cost arithmetic, and exact uninformative fallback equality. Source and output hashes are recorded in `RUN.md` after execution.
