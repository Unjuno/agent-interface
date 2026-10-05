# Issue #7808 A01 — retained-route eligibility check

**Disposition: `HOLD_NO_ELIGIBLE_COHORT`.** This is a read-only qualification for the proposed empirical successor. It does not revise the A01 synthetic result or authorize a live/model/GUI allocation.

## H / T / D / C / U

- **H:** Current retained #59 evidence contains a repeated, comparable route-opportunity cohort with source-bound soft-cost vectors and independently scored useful effects sufficient for a read-only transfer check.
- **T:** Inspected the current-main v38/v39 control-tempo posthoc report and analysis, plus the referenced v39 report, raw `runtime/events.jsonl`, and `retention-manifest.json`, at main `dccf55e264f434ca27f2948fe53be09919047819`. The posthoc analysis records SHA-256 `719db21040b843c5c91c5ff1f3d9fb2051ae1f1e008971547f39f015b4337687` for v39 `report.json` and `2c917658e8bba0a94e5a34f0ee3d968553cd56950105196871012f2e3eedb381` for `runtime/events.jsonl`; independent streamed hashes and the current retention manifest agree.
- **D:** **HOLD.** The inputs are source-bound, but the eligibility conditions are not met:
  1. v38 and v39 are two stochastic first-outcome episodes with different model actions, cover policies, and completion patterns, not matched assignments of the same route choices under comparable opportunities.
  2. The posthoc report measures accepted program envelopes intersected with planner waits. It explicitly does not measure actual physical key-down occupancy.
  3. Typed health deltas and viewport-change receipts are not independently scored useful effects attributable to each route opportunity. The retained final scores are episode-level (v38: 0 kills/no exit; v39: 1 kill/no exit).
  4. Missing/unfinished planner turns remain part of the denominator; they cannot be dropped or imputed.
  5. The posthoc report itself characterizes the episodes as stochastic with different model actions and says there is no causal, survival, useful-feedback, or human-tempo comparison.
- **C:** More detailed private or unpushed traces may exist; this check covers the visible retained v38/v39 source package only. A future source-bound, instrumented, matched cohort might satisfy the gate.
- **U:** This is an eligibility audit, not a new empirical comparison. It does not infer that route adaptation lacks value, and it does not identify why the two runs differ.

## Evidence inspected

- [Posthoc report at the checked main commit](https://github.com/Unjuno/agent-interface/blob/dccf55e264f434ca27f2948fe53be09919047819/research/doom/MAP01_V38_V39_CONTROL_TEMPO_POSTHOC_V1.md)
- [Posthoc analysis JSON](https://github.com/Unjuno/agent-interface/blob/dccf55e264f434ca27f2948fe53be09919047819/research/doom/results/map01-v38-v39-control-tempo-posthoc-v1/analysis.json)
- [v39 report](https://github.com/Unjuno/agent-interface/blob/dccf55e264f434ca27f2948fe53be09919047819/research/doom/results/map01-v39-coast-liveness-live-01/report.json)
- [v39 retention manifest](https://github.com/Unjuno/agent-interface/blob/dccf55e264f434ca27f2948fe53be09919047819/research/doom/results/map01-v39-coast-liveness-live-01/retention-manifest.json)

No candidate, auditor, test, model, game, GUI, container, or external effect was run for this eligibility check. **Do not promote the A01 synthetic PASS to real route benefit.** A T1 comparison remains gated on a newly authorized, comparable cohort with complete source-bound route costs and independent per-opportunity effect scoring.
