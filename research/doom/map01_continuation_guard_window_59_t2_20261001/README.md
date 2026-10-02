# Retained continuation-guard window diagnostic

This is a posthoc timing analysis of retained v39 decision 2 for Issue #59. It
does not replay the game or infer key occupancy. Read [PLAN.md](PLAN.md),
[REPORT.md](REPORT.md), and [FREEZE.json](FREEZE.json) for scope, hashes, and the
execution deviation. The candidate raw summary and independent raw-only audit
are under `results/`.

The narrow result is that typed health first fell below the decision-2 source
health of 85 at sequence 76, during a 6.307-second model wait. The typed row's
producer-side emit timestamp leaves about 4.804 seconds before model return.
This is a counterfactual guard boundary only: the retained run used unauthored
coast, not the hypothetical admitted continuation policy.
