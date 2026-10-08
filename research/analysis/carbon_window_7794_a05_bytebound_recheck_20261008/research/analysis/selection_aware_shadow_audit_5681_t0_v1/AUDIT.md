# Read-only audit details — Issue #5681 T0

## Selected source

One O1 episode: `research/observation_gating/results/fresh-a1r3-r1/calc-490101-O1/`.
The path was selected from the canonical A1 report's retained fresh-replicate
links and completed-run manifest. It is not a new run.

## Checks executed

Read-only Git object commands against `origin/main` at
`3d2dc70a239ff41650438a7d441bb08a094d6272`:

```sh
git show origin/main:research/observation_gating/results/fresh-a1r3-r1/calc-490101-O1/observations.jsonl
git show origin/main:research/observation_gating/results/fresh-a1r3-r1/calc-490101-O1/result.json
git show origin/main:research/observation_gating/results/fresh-a1r3-r1/COMPLETE.json
git show origin/main:research/observation_gating/gui_suite.py
git show origin/main:research/observation_gating/exact_gate.py
```

The JSONL audit parsed all 7 rows and checked:

- identity/order: `sequence` is present for 7/7;
- action association: `action_id` is present for 7/7;
- time: `observed_ns` is present for 7/7; source assigns it from
  `time.perf_counter_ns()`;
- decision: boolean `suppressed` is present for 7/7; counts are 4 false / 3 true;
- gate reason: `reason` is present for 7/7;
- independent semantic/event/error label: 0/7 rows contains any of
  `semantic_label`, `semantic_transition`, `independent_label`, `frame_label`,
  or `event_label`.

The episode result JSON reports `candidate_observations=7`,
`model_visible_observations=4`, `suppressed_observations=3`,
`false_suppressions=0`, `missed_changes=0`, and a single terminal workbook
oracle (`success=true`, actual cells `[883,147]`). The terminal oracle is not a
per-capture label. No observations were imputed or relabeled.

The per-capture files are auditable and complete for the original A1 gate
question, but do not meet #5681's separate selection-bias estimand contract.
