# Candidate and bundle evaluation contract

Status: design only; no qualifying individual or bundle gain is established.
This implements the [user's revision](source_freeze_revision_proposal.md).

## Predeclare a finite, justified study

Select candidates by unresolved failures, distinct bottlenecks, architectural
uncertainty or cross-domain transfer. Retain small reproducible low-cost gains.
Record compatible combinations, exclusions with reasons, available study budget,
metric-specific minimum meaningful movement, uncertainty method and stopping
review before results. Budget exhaustion alone is not evidence of saturation;
unmeasured plausible high-value combinations remain an open question. Amendments
start a separately identified study rather than changing gates after results.

For two candidates compare baseline, A, B and A+B using pinned source/adapter
hashes, the same model/settings/output limits, tasks, seeds and environments.
Counterbalance order, retain failed attempts and recovery, and declare sample
allocation and paired uncertainty analysis. Larger bundles need ablations that
can resolve the nominated overlaps or synergies. A historical result on another
baseline is not an arm of this study. Shared correctness gates apply to every arm.

## Measured gain and interaction

For positive baseline metric M0 and candidate Mc, store gains as fractions:
cost/latency reduction = 1 - Mc/M0; throughput gain = Mc/M0 - 1.
Declare units, direction, endpoint and aggregation. Undefined ratios stay missing.
Only an executed combined arm supplies bundle_gain; sums and products are not
measured combined evidence. JSON bytes cannot substitute for actual model tokens.

A predeclared multiplicative independence reference predicts cost reduction
1 - (1-gA)(1-gB), or throughput gain (1+gA)(1+gB) - 1.
interaction_effect = measured bundle_gain minus that prediction, stored as a
fractional difference (multiply by 100 for percentage points). Include joint
uncertainty, including shared-baseline covariance. Its sign alone does not prove
overlap or synergy. Use another justified reference only if declared in advance.

Illustration only: cost reductions of 6% and 5% predict 10.7%. Measured 6.8%
would differ by -3.9 percentage points, and 15% by +4.3 points. These are examples,
not Agent Interface measurements. Five independent 8% reductions predict 34.1%,
but independence and the resulting real combined gain still require measurement.

## Frontier and decision record

Assess task correctness, wrong-target/stale input, planner boundaries, end-to-end
latency and supported p95/p99, actual tokens, observations, recovery cost and
implementation complexity. Keep units separate. Only correctness-passing arms
are eligible. Point estimates alone cannot establish dominance: report uncertainty,
missing axes and material tradeoffs. A new useful tradeoff can move the frontier
without dominating every existing point. Predeclare tolerances and meaningful
improvement on relevant axes; never create a weighted score after seeing results.

Record complexity as a reviewed change vector: semantic primitives, input/owner
paths, maintenance burden, regression exposure and portability cost, with evidence.
Do not subtract lines of code or subjective risk directly from milliseconds.
Record net_decision with rationale: RETAIN, PROMOTE, HOLD, DEFER or REJECT.
PROMOTE requires the declared correctness and replication gates, not just 10%.

Review remaining individual AND bundle frontier movement across at least three
qualifying revisions alongside failure discovery, regression and core semantic
churn. Cross-domain correctness remains mandatory. A missing study or imprecise
estimate cannot establish small remaining gain. Research Freeze nomination is
a recorded judgment, not automatic completion of the human-tempo product goal.

## Ledger schema and provenance

`evolution.csv` is a generated historical revision index. Its new fields are
unknown until supported, and must not be hand-filled because rebuilding replaces
them. Store future studies in `bundle_evaluations.csv`, one row per arm/metric,
with a stable study_id, candidate_id, bundle_id and members. Link the complete
predeclared manifest and raw results through evidence; uncertainty and complexity
fields may reference detailed artifacts. The builder does not overwrite this file.

- individual_gain: measured single-arm fractional gain; blank for bundles.
- bundle_gain: measured combined-arm fractional gain; blank for individual arms.
- interaction_effect: fractional difference from the named reference model.
- complexity_delta: reviewed vector or evidence link, not a fabricated scalar.
- new_core_semantics: explicit additions or audited `none`; blank is unknown.
- net_decision: decision plus rationale in the linked review.

All metric rows of an arm must be reviewed together. Existing best_marginal_gain
remains a legacy supplementary field; do not silently populate it with a different
metric or infer a Pareto frontier from its chart. A header-only bundle register
means no measured bundle study, not zero remaining gain.
