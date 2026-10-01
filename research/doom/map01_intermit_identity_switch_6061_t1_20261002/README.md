# Issue #6061 identity-switch T1

This is an additive finite-method successor to the T0 result in PR #6084. It executes the previously planned semantic identity-switch negative control: zero motion-prediction error, with separate visible-ID, evidence-epoch-only, unknown, and observationally silent switches.

The candidate sees only input.json. The independent raw-only auditor sees the separate truth.json. commanded_occupancy_ticks counts synthetic fixture commands only and is not physical input occupancy. No model, GUI, game, X11, user data, network, or live allocation is involved.

See PLAN.md for H/T/D/C/U and frozen gates, FREEZE.json for source/input/image identities, RUN.json and raw outputs under results/allocation-01/ for the one-shot result, RESULT.md for interpretation, CONTAINER_INVOCATION.md for the exact bounded launch, and SHA256SUMS.txt for artifact verification. The T0 in PR #6084 and all retained MAP01 outcomes remain unchanged.
