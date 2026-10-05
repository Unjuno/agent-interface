# Decision-value acquisition calibration boundary — T0 A02

This is a successor allocation to #7934 A01, which remains a frozen FAIL_AUDIT.
It changes the estimand to model/true likelihood calibration and uses a
parameter grid rather than the prior three-profile comparison. The GitHub
Issue #7934 A02 preregistration comment is authoritative.

The two hard-gate-admitted routes are A (utility 1 iff X=0) and B (utility 1
iff X=1), with prior P(X=0)=P(X=1)=1/2. Independent balanced Y has no route
utility. A direct check reports X with true accuracy qt; a perfect nuisance
check reveals Y. The candidate's direct-check model accuracy is qm.

Policies: cost-only selects the cheapest check within budget. Entropy selects
the available check with greatest mutual information about complete hidden
state (X,Y), using qm for direct-check likelihood; ties resolve by check ID.
Decision-value computes one-step EVSI under qm minus direct-check cost and
selects direct X only for strictly positive net value; it otherwise stops.
The oracle uses qt and the same rule. Route posterior after direct X uses qm
for decision-value and qt for oracle; cost/entropy baselines use the check's
declared likelihood (perfect Y has no X information), with route ties to A.

Grid: qt and qm each in {0.2,0.4,0.6,0.8}, direct check cost in {0.02,0.12};
128 paired deterministic SHA256 draws per each of 32 cells, 4096 rows total.
Draw key is `7934-T0-A02|qt=<qt>|seed=<seed>|stream=<x|y|noise>`; convert the
first 13 hex digits to a uniform value by dividing by 16^13. X and Y are
balanced; direct signal equals X iff noise < qt. The same latent/noise draws
are shared across qm and cost cells at each qt/seed.

The auditor dynamically recomputes choices from each cell, every draw, sampled
regret/cost, exact expected regret/cost, gate violations and controls. It uses
no frozen expected-choice matrix. On qm=qt cells, decision-value must choose
the same check/stop as oracle and match exact regret-plus-cost. Marked
distribution shift and 0.10 unmodeled-mass controls return UNKNOWN with zero
checks. Unmarked qm != qt cells are sensitivity analysis, not a shift-detection
claim.

Execution: one WSLc 3.0.1.0 launch, pinned locally cached Python 3.12.15 digest,
network none, one configured CPU, read-only source, writable output, zero
retries. CPU quota enforcement is not inferred from configuration. CPU-only is
appropriate; no GPU, GUI, model, task or user data is involved.
