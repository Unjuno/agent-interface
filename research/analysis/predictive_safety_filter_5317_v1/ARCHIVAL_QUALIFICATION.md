# Archival qualification: #5317 host-only finite safety filter and withdrawn container rung

This is an additive preservation note for the six unchanged published files from [Draft PR #5336](https://github.com/Unjuno/agent-interface/pull/5336), head `c04150c5884b4b6069427e0ea7c275c1d9f94320`, branch `research/safety-filter-5317-t0-20260930`. Source preservation does not complete the requested container rung, close the source Draft or [owner #5317](https://github.com/Unjuno/agent-interface/issues/5317), modify its branch, or grant any new execution/resource authority.

## Preserved evidence and byte identity

The complete source directory at that commit contains `safety_filter_5317.py`, `test_safety_filter_5317.py`, `run_safety_filter_5317.py`, `audit_safety_filter_5317.py`, `safety_filter_5317_raw.json`, and `safety_filter_5317_protocol.md`. All six archived byte sequences reproduce their source Git blob IDs and all six SHA-256 claims in [owner comment 5907878393](https://github.com/Unjuno/agent-interface/issues/5317#issuecomment-5907878393). The original directory tree is `50d88c7a120f4239fe274fb85c34c28f2d9582a9`; each source file has mode `100644`.

The committed raw is present: SHA-256 `fef9450c33cd227f794d6146a88fea7c89fad31b1758e800bff04d796935e611`, with seven scenario objects and five policy cells per scenario (35 cells). Its metadata says `host-only-construction`, horizon 2, source main `70b69b47845b35afde59c2a5f0b56c6f906c6904`, and `container_invocations: 0`. These are retained artifact contents, not a fresh execution receipt.

The protocol and owner comment report 7/7 host tests and a separate `PASS_READONLY` audit of 35 cells with zero errors. Their reported disposition is `PASS_HOST_FINITE_DISCRIMINATOR_SCOPED / HOLD_NO_EXACT_SLOT_FOR_CONTAINER_RUNG`. Preservation verifies bytes and reads the recorded inventory; it does not rerun tests, the runner, the auditor, or a scientific experiment. The six-file package contains no separate machine audit-output receipt, stdout log, runtime/platform attestation, or machine `FREEZE.json`. The owner hash comment was published at 2026-09-30 09:04:09 UTC, after the protocol's reported 09:03 host result, so these matching published hashes alone are not proof of a pre-execution source freeze.

## Later container withdrawal controls interpretation

The protocol records an empty OrbStack inventory at 08:59:45 UTC and a pinned local image `python:3.13.5-slim-bookworm` with ID `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419`. Those statements describe the earlier historical check, not current availability or a granted slot.

The later [owner comment 5907959516](https://github.com/Unjuno/agent-interface/issues/5317#issuecomment-5907959516), published at 09:08:55 UTC, records that a read-only 2026-09-30 09:07 UTC inventory found running container `cans-hg-n64-dt0.00025-addendum`, ID `51940c4b3e81e5d5dc02a4c596c798935e20f90d048a3c61f1e461b44c17f4af`, with unknown owner; it was left untouched. Inspecting the pinned Python image returned blank OS/Architecture metadata. The proposed 09:15–09:30 request was withdrawn pending resource-owner reconciliation and platform verification. The owner explicitly retains zero #5317 container invocations and host-only evidence as the sole executed rung for this original allocation.

Accordingly, this archive retains the host evidence and the later STOP/HOLD/withdrawal together. The unchanged protocol's conditional reproduction instructions are historical plans, not permission to resume them. No shared resource was inspected, claimed, started, stopped, or retried by this preservation work. No host result may be relabeled as Docker/OrbStack evidence.

## Static dependency and interpretation limits

These observations come from reading the preserved source; no additional cases or mutations were run.

- The runner imports `CASES` from the included test module and `POLICIES`/`run_case` from the included simulator. The tests import the simulator. Other imports are Python standard-library `collections`, `json`, `sys`, and `unittest`; the independent auditor imports only `json` and `sys`. The six-file package contains these local module dependencies, and no external Python package dependency is declared by these sources.
- `HORIZON_FILTER` obtains the state set after `actions[:horizon]` and checks that returned set for forbidden states. It does not separately test every earlier intermediate state for forbidden membership. The retained two-step case places `BAD` at that checked endpoint; the seven-case result must not be generalized to all possible unsafe intermediate-prefix shapes.
- `_has_recovery` is an existential graph search with default depth bound 8. It is not a proof that a recovery controller robustly succeeds under every nondeterministic outcome or unbounded continuation.
- The raw-only auditor compares a hand-written expected Boolean outcome matrix plus scenario/policy inventories, zero container metadata, and false authority/effect fields. It does not independently replay transition graphs or verify source hashes, reason strings, or all input/metadata fields. Its reported `PASS_READONLY` has this specific scope.
- `authority_created` and `effect_claim_created` are constant false fields in the finite simulator. Their values establish no live authorization or real-world effect safety.

No source, raw cell, protocol wording, or historical result has been repaired or promoted. Runtime model completeness/currentness, real GUI action semantics, intent preservation, recovery effectiveness, and production safety remain unvalidated.

## Distinct later allocation and navigation

Merged [PR #5505](https://github.com/Unjuno/agent-interface/pull/5505), merge commit `2188d11aedac87d3e1e92ca25a7d1b5d4f593e90`, added the distinct `predictive_safety_filter_5317_t3_v1/` allocation. That eight-artifact T3 package is present on main `e12e4e2939890d735cb1b11df3a8d8b6a1cf4b9a`; the original `predictive_safety_filter_5317_v1/` directory was absent at the archival intake check. T3's different source, enumeration, audit, and disposition neither deliver this original six-file package nor supersede its withdrawn container request.

The archive is listed in the historical-source section of the analysis index. It deliberately does not add a new `REPORT.md`, `FORMAL_FAILURE.md`, or generated-result-index entry. This qualification is separate from the unchanged historical files and creates no new scientific result.
