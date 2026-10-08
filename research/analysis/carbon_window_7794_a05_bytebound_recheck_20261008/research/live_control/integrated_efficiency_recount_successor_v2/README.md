# Recount successor v2

This package independently rechecks the retained #57 integrated-efficiency
accounting record and addresses three concrete review counterexamples on the
merged v1 recount: unbound evidence-root provenance, trust in a precomputed
`exact` flag, and duplicate raw result IDs silently overwriting each other.

It is deliberately additive. It does not edit the original study, v1 auditor,
V8 recount, or any historical result. `PLAN.md`, `FREEZE.json`, and
`INPUT_MANIFEST.json` define the frozen audit. A host-only result is not Docker
parity and is not a new model/task/efficiency sample.
