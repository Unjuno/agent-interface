# Research convergence and freeze review

Status: **NOT READY — evidence incomplete**, not a failed product and not a
completed architecture phase. This adopts the user's convergence proposal;
the numeric gates below are initial working criteria, not measured outcomes.

## Review contract

Before the next promotion study, declare the reference runtime/semantics,
baseline, primary metric, task allocation, held-out cases, stress conditions,
measurement clock, sample size rationale and correctness criteria. Candidate
selection and any threshold changes must precede viewing that study's results.

Use a rolling window of at least three qualifying major revisions to nominate
a Research Freeze Candidate. A qualifying revision executes the declared shared
evaluation, not just its new feature's unit tests. Three zero-count toy probes
or three documentation revisions cannot qualify.

All of these must hold together:

- No newly observed failure class in the window, under comparable fresh/stress
  coverage. Unreviewed logs and missing exposure are unknown, never zero.
- No observed regression in the declared previously passing invariants; no
  unresolved correctness-blocking recurrence. Report denominators and uncertainty.
- No core protocol/runtime semantic change (churn score 3); the work is mainly
  engineering/tuning. A low count cannot override an unresolved architecture issue.
- Tested architecture candidates no longer exceed the predeclared meaningful
  improvement threshold. Working starting point: 10% on one nominated primary
  metric, with correctness gates and uncertainty considered. Bytes cannot stand
  in for model tokens; incomparable metrics cannot be pooled into one gain curve.
- The **same candidate semantics** pass terminal/text, browser, spreadsheet,
  graphics/editor, multi-window/modal, continuous motor and real-time DOOM checks.
  Historical successes from different runtime revisions do not establish this.
- Fresh/held-out/stress checks cover task success, wrong-target and stale input,
  held-input cleanup, critical-event retention and recovery. Define acceptable
  rates and exposure before running; a few zero incidents do not prove zero risk.

The volume and statistical acceptance criteria for that shared evaluation remain
to be specified. Until then no revision qualifies for the rolling freeze window.
Declining discovery can also reflect weaker testing or a coarse taxonomy, so
coverage and taxonomy changes must accompany any curve.

Research Freeze Candidate triggers a recorded review, not automatic promotion.
Research Freeze ends Phase A only. Phase B consolidation and Protocol Freeze
require a distinct review. Windows/macOS implementation starts when core input,
lease, release, focus, observation/event, stale-action, input ISA and planner
boundary semantics are stable and separable from X11. Final product/human-tempo
claims still require the original goal's evidence.

## Ledger and chart rules

`evolution.csv` indexes raw records without moving them. Empty numeric fields
mean unknown/not established; zero requires audited coverage. Historical rows
are explicitly partial. Churn scores are reviewer judgments: 0 implementation,
1 minor semantics, 2 subsystem semantics, 3 core protocol/runtime semantics.
Decision HOLD is not failure; functional PASS is not product PROMOTED.

Next deliverables: complete historical backfill; an occurrence-level failure
register; `generate_curves.py`; separate charts for cumulative discoveries,
discoveries/revision, regressions, churn, comparable marginal gains, success,
p95/p99, boundaries/success, observations/success, wrong-target/stale incidents.
Missing data must appear as gaps or 'not measured', never flat zero curves.
Latency plots require a named endpoint/clock and enough samples; do not turn
single exploratory trials into p95/p99 estimates.
