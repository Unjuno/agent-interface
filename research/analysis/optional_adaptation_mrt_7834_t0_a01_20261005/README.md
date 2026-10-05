# Issue #7834 T0 A01 — carryover-aware optional-adaptation estimator

This package tests the finite-method hypothesis in [Issue #7834](https://github.com/Unjuno/agent-interface/issues/7834). It is an exact enumeration of two synthetic session clusters × four decision times, not an online experiment or an interface treatment result.

## Frozen question

Does the known-propensity availability-aware excursion estimator recover the exact marginal proximal effect, including a predeclared prior-execution stratum, when availability, assignment probability, carryover, and nonexecution depend on observed/latent history? Do the unweighted history-ignorant and executed-only controls fail on their designated confounding conditions? Are support, eligibility timing, missing outcome, cross-session interference, and proximal/distal inversion handled without bypassing mandatory controls?

## Scope and environment

The optional adaptation is purely synthetic, reversible, presentation-only, and non-authoritative. Required observation, freshness and release controls are held byte-identical in all records. No GUI, model, user data, action, network call by the candidate, or external effect occurs.

OrbStack's Docker API is reachable, but the local image store cannot read/pull content blobs (`operation not supported`). No shared daemon repair/restart or image mutation was attempted. Since the frozen T0 is a deterministic standard-library CPU model with no container-dependent behavior, it runs on host CPython 3.14.5 as an explicitly host-only fallback; there is no claim of container isolation, cgroup limit, or swap enforcement. Exact diagnostics are in `ENVIRONMENT.json`.

## Reproduction

1. Verify `FREEZE.json` source SHA-256 values.
2. Construction only: `python3 -B -m unittest -v research.analysis.optional_adaptation_mrt_7834_t0_a01_20261005.test_construction` (5 tests, run before freeze).
3. Formal candidate once: `python3 -B research/analysis/optional_adaptation_mrt_7834_t0_a01_20261005/candidate.py --output research/analysis/optional_adaptation_mrt_7834_t0_a01_20261005/results/candidate.raw.json`.
4. Independent auditor once: `python3 -B research/analysis/optional_adaptation_mrt_7834_t0_a01_20261005/audit.py --raw research/analysis/optional_adaptation_mrt_7834_t0_a01_20261005/results/candidate.raw.json --output research/analysis/optional_adaptation_mrt_7834_t0_a01_20261005/results/AUDIT.json`.

Do not repeat either formal invocation. Retain any first failure unchanged; a correction requires an additive successor allocation.

## Artifacts

- `PROTOCOL.md`, `fixture.json`, `FREEZE.json`: decision gates and preregistered inputs.
- `candidate.py`, `audit.py`, `test_construction.py`: separately implemented paths and pre-freeze check.
- `results/candidate.raw.json`, `results/AUDIT.json`: immutable formal outputs.
- `REPORT.md`, `SHA256SUMS`: disposition, commands, and integrity manifest.

## Claim ceiling

Even a method PASS is exact reconstruction of this authored finite model only. Two clusters do not support population inference; proximal effect is not a surrogate for episode success; no real assignment, carryover, user adaptation, GUI correctness, latency benefit, safety, or deployment claim follows.
