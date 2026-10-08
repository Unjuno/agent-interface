# Issue #5504 T0 — synthetic refinement boundary

This package tests a finite, model-free counterexample-guided refinement harness. It is not a runtime verifier or a product change.

The frozen 8/8 train/held-out cases cover independent authority, target, evidence-currentness and effect predicates plus dependency cycles. Candidate arms are a coarse one-check abstraction, replay-guided CEGAR, a complete five-check static ontology, and an intentionally over-specific eight-check static gate. Malformed and ambiguous cases are expected to remain `UNKNOWN`.

See [PLAN.md](PLAN.md) for H/T/D/C/U and preregistered gates, [FREEZE.json](FREEZE.json) for source/image identity, and `results/t0/` for the one-shot result and independent audit after execution. A PASS is limited to this synthetic corpus; it does not demonstrate usefulness or safety on actual agent-interface traces.
