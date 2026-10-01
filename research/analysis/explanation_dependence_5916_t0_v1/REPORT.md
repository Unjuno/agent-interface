# Issue #5916 T0 — explanation-dependence audit

**Disposition: `PASS_METHOD_SCOPED`; additional perturbation layer `NOT JUSTIFIED` against the exact-trace baseline in this finite fixture.**

This was one frozen, synthetic CPU-only run. Candidate and independently implemented truth-table auditor each ran once. Ten bundles covered necessary citation, two alternative DENY predicates, independent alternative proof DAGs, context-only citation, an uncited decisive blocker, stale epoch, valid contradictory replacement, invalid mandatory deletion, and policy swap with unchanged rationale.

## Result

- 10/10 candidate dispositions matched the independent oracle; 0 audit errors.
- All 4 planted unsupported/insensitive explanation cases were flagged; all 5 valid explanation cases were accepted.
- The illegal deletion returned `UNTESTABLE`; it was not interpreted as causal evidence.
- Both independent proof DAGs were accepted, and removing either proof still left the union policy at `ALLOW`.
- The exact machine-produced trace reconstructed every frozen policy decision, including the independent proof union. The perturbation audit exposed no defect-detection coverage beyond that exact trace in this fixture. This supports the counter-hypothesis: when a deterministic complete policy can emit a correct bound proof trace, an extra perturbation layer has no demonstrated incremental value here.

## Scope and limits

This only validates a small typed synthetic method. It does not establish faithfulness of model explanations, completeness of live interface receipts, human comprehension, production suitability, or causal internals. The audit implementation has explicit fixture-specific defect checks; no statistical generalization is possible from ten designed cases. Exact-trace dominance assumes the policy and dependencies are completely captured and the trace generator is trusted; hidden mutable state and incomplete policies remain outside the test.

Docker Desktop was not used: its daemon was observed stopped and no Issue-specific shared resource lease was available. The fixture had no external effects and ran on host CPU. This is a documented execution choice, not a Docker experiment.

## Reproduction

From this directory with Python 3.12: `python -m unittest -v test_construction.py` (construction suite, 5/5); formal candidate command `python candidate.py`; preserve its exact JSON output as `candidate_output.json`; then run `python auditor.py` exactly once. The retained outputs are `candidate_output.json` and `audit.json`; source freeze is commit `2d2785f1619c98b103b7f1a4f5abb9f32da49476`.
