# Issue #5309 A11 — topology-dependent witness dynamics

This additive successor tests whether a witness-aware choice policy follows the actual transition graph when deciding which action preserves a proof receipt. It corrects A10's construct-validity limitation: in A11, witness survival is computed from each topology's destination state, and the preserving action varies by state and graph.

## H / T / D / C / U

- **H:** Given equal information gain and the same admissible action set, a witness-aware chooser using an affordable, correct witness-survival prediction will yield more independently reconstructed completions than a lexical generic chooser. Under misspecification it must not claim completion without a real witness; over-budget preservation falls back to generic choice; a preexisting witness is a control.
- **T:** 132 deterministic cases across cycle-3, branch/merge-4, and asymmetric-4 directed transition graphs; all states, correct/misspecified predictions, preservation costs 0/1/2, and prior witness absent/present. There are two actions per case and 264 arm rows. The environment's survival outcome is derived from the selected edge's destination and the graph's witness state. Host CPython; separate CLI processes, but no OS-level oracle isolation.
- **D:** Formal PASS only if the auditor independently reconstructs all 264 arm rows exactly, reports zero errors and zero authority grants, confirms three distinct topology-to-preserving-action signatures, finds a strict WITNESS completion advantage in correct/affordable cases, finds no WITNESS completion in misspecified cases, and confirms equality for over-budget and prior-witness controls. Otherwise retain FAIL/STOP without rerunning the allocation.
- **C:** Deterministic, authored finite-state fixture; predictions are intentionally perfect or inverted. This is a method/construct check, not an estimate of natural-world prevalence or cost.
- **U:** No live application/GUI, model, physical input, calibrated cost, latency, user task, authority, or product-level evidence.

The historical A10 report remains unchanged and explicitly documents its topology-invariant witness mapping and formal auditor failure. A11 is a successor allocation, not a rewrite of that result.

See `PRE_RUN.md` for the frozen commands and `REPORT.md` for the outcome.
