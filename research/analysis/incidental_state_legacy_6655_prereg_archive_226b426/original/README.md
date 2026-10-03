# Issue #6655 — incidental-state legacy T0

Status before formal invocation: frozen synthetic method test; no real application or user state is involved.

This package tests whether an inherited incidental interface-state delta can be distinguished from beneficial, harmful, irrelevant, required, incompletely restored, shared/external, or task-mismatched state. It uses paired exact-seed later tasks, explicit state diffs, randomized arm order, and a separate auditor. Full H/T/D/C/U and stopping rules are in [`PREREGISTRATION.md`](PREREGISTRATION.md); immutable source/runtime identities are in [`FREEZE.json`](FREEZE.json).

The nine local construction tests passed before freeze (including six mutation/ineligibility controls). Formal candidate/auditor invocations are not represented by those tests. Results and command evidence will be added only after the one-shot candidate and separate audit finish.

Scope: finite synthetic CPU fixture only. No model, GPU, GUI, real workspace/settings, container, network call, or user/external effect. A method PASS would validate only reconstruction and the seeded controls; it would not establish a real-interface carryover effect or close #6655.
