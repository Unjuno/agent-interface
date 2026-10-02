# Issue #6691 T0 freeze

Status: `PREREGISTERED_NOT_RUN` until the source and protocol hashes are frozen.

## H / T / D / C / U

- **H:** A named mechanism arm that pools outcome-relevant versions with coalition-dependent proportions can yield a different pooled contrast than the same contrast standardized to a common version distribution. Version-explicit reporting can expose the changed estimand without modifying task-effect or safety truth.
- **T:** Deterministic finite 2-factor table; factor A has two versions, factor B two versions; retain task effect and safety as separate columns. Include equal-effect, version-interaction, unequal-mixture, a structurally infeasible cross-version cell, missing attempt and unknown-version rows. Candidate emits raw rows and descriptive calculations. A separately implemented raw-only auditor reconstructs all values. Mutation controls cover relabel, dropped failure, altered mixture, infeasible-cell imputation, and scalarized safety.
- **D:** `PASS_METHOD_SCOPED` only when independent raw-only reconstruction agrees, the equal-effect A-version control at `B=off` has equal pooled/standardized contrast, the version-interaction case at `B=off` separates them, the structural-zero A2×B2 cell is excluded from common support and retained as unassigned (not imputed), and missing/unknown rows remain unresolved; applicable corruptions are rejected; task effect and safety remain invariant/separate. `B=on` pooled-vs-standardized values are descriptive because the structural zero changes joint B-version support even under equal A effects. `FAIL_METHOD` for silent pooling that changes the declared target, fabricated support, or safety/outcome conflation. `HOLD` if identity/support/reconstruction is unresolved.
- **C:** A fixed stochastic version policy assigned identically across all coalitions may make the pooled policy-level estimand appropriate; stratification may add no value.
- **U:** Authored finite rows demonstrate only a method counterexample/control. No claim that prior repository comparisons are biased, that software versions are semantically equivalent, or that any runtime/product effect exists.

## Execution freeze

- Issue: https://github.com/Unjuno/agent-interface/issues/6691
- Main base at intake: `8c06589df01b2c4c1ab4017744faca61cab729f8`; fast-forwarded to latest main `c8e8bccd6dd96fda518111b526bd499582186566` before formal freeze (changes confined to other evidence paths and index/ledger).
- Branch: `research/version-defined-intervention-6691-orbstack-t0-20261002`
- Additive path: `research/analysis/version_defined_intervention_6691_t0_20261002/`
- Runtime: OrbStack Docker; image `python:3.12-slim-bookworm`, pinned by local image ID/digest at freeze.
- Candidate and auditor are separate no-network containers. Inputs are read-only; only the dedicated output mount is writable. Container settings do not prove effective CPU/memory enforcement; record host/cgroup caveats.
- Formal candidate/auditor each run once after source/protocol freeze. No retry or repair after formal invocation.

## Pre-formal gates

Construction tests are not formal allocation. Verify syntax, exact hand-calculated fixture facts, independent arithmetic, each mutation's expected rejection/UNKNOWN classification, and clean out-of-path collision scan before source hash freeze. Record commands, identities, stdout, exit codes and SHA-256 after the one-shot run.
