# Evolution index and convergence review

This index is deliberately scoped. It currently reconstructs seven recent
revision groups, eight actual assistant tasks (seven independently successful,
one failed), and nine selected observed failure occurrences across four taxonomy
classes. It is not a census of all Agent Interface research.

The original four-row ledger omitted the earlier failed Calc self-use cohort.
That cohort is now included as `owner-v5` (1/2 success); the task-description
follow-up is separately `owner-v6` (1/1). No historical raw result was changed.
Same-commit groups represent different measured runtime revisions, not separate
commits. Controlled probe episodes do not enter saved-task success denominators.

## Rebuild

With Python and matplotlib available (generated with matplotlib 3.10.6):

```sh
python research/evolution/build_index.py
python research/evolution/generate_curves.py
```

`build_index.py` checks archived events against existing audit summaries, hashes
its input files, and regenerates the scoped ledger, session index, occurrence
register and backfill audit. It does not rerun GUI actions or replace the original
frame/workbook auditors. `generate_curves.py` generates ten separate charts.
CSV blanks become missing points. Global discoveries, primary-metric gains,
latency tails and planner boundaries currently show missing-evidence panels.

Files:

- `evolution.csv`: revision groups and scoped metrics.
- `sessions.csv`: exact self-use cohort membership and denominators.
- `occurrences.csv`: selected observed failures, with evaluation and introduced
  revisions separated. Four delayed-release cases are baseline controls; two
  wrong-target cases are baseline controls; two recovery failures represent one
  regression class introduced by focus binding; one Calc task was misinterpreted.
- `backfill-audit.json`: source hashes, coverage counts and unknown status.
- `charts/`: descriptive views, never an automatic freeze decision.
- `evaluation_plan.md`: next shared-evaluation preparation, including blockers.

Global first-discovery ordering and exhaustive recurrence/regression coverage
remain unreviewed. For that reason `new_failure_classes` and
`known_failure_recurrences` remain blank; nine indexed occurrences cannot be
relabelled as nine new discoveries. One known introduced regression class is
recorded for focus; blank values elsewhere do not imply regression-free changes.
Ratings of architecture churn remain explicitly retrospective human/agent
judgments. The recent downward sequence is not proof of long-term convergence.

Charts were visually inspected for readable missing-data and success panels.
The tiny and heterogeneous self-use cohorts do not support p95/p99, success-rate
generalization, or a promotion-gain curve. No revision qualifies for the shared
freeze window yet. Next backfill targets are pre-owner lease, decision boundary,
event retention, visual tracking, DOOM, A1/A2 and early route/motor failures.
