# Raw evaluation-artifact bypass — Issue #8581 T0 A03

The corrected finite method fixture passed independent audit. Candidate and auditor each ran once; the auditor reconstructed all four cells / 92 events with zero errors and rejected all five frozen mutations.

- Frozen disposition: `BYPASS_DEFEATS_FEEDBACK_SCOPED` under the preregistered equality-inclusive rule.
- Observed cells: all selected candidate 5; development accuracy 17/24, fresh accuracy 119/256, optimism 0.2435.
- Interpretation: all four cells are identical, so there is no evidence that bypass itself changed the result; controlled feedback showed no advantage over full feedback in this fixture.
- A01 and A02 STOP/HOLD first outcomes remain preserved and are not pooled.

See `FREEZE.json`, `REPORT.md`, `EXECUTION_RECORD.json`, `run-01/`, and `SHA256SUMS.txt`.
