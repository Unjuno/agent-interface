# Issue #5686 T2 — metric-guided policy selection feedback

This package tests the prospective T2 idea in #5686: selecting an interface policy by an intermediate metric can alter observation availability and thereby change which outcomes are visible. It separately includes an authored selection-overfit control so a selection-set winner is not mislabeled as a performative distribution shift.

The finite fixture has four worlds, three policies per world, four fixed strata, two disjoint splits, and two opportunities per stratum: 192 attempt rows plus four selection summaries. The candidate emits every opportunity, including unavailable observations and unsafe outcomes. A separate auditor reconstructs the complete inventory and recomputes both selection rules from raw JSONL without importing the candidate.

`PASS_SELECTION_FEEDBACK_GATE_SCOPED` means only that the gate distinguishes the frozen synthetic controls as specified. It validates no real metric, adaptive interface, task population, or transport claim. See `PREREGISTRATION.md` and, after formal execution, `RESULTS.md`.
