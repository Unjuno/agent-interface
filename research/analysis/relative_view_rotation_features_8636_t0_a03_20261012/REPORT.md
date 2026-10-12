# Issue #8636 T0 A03 — first outcome

**Disposition: `HOLD_UNCERTAIN`.** The candidate completed its one frozen invocation (360 planned arm trials, exit 0). The independent auditor completed its one allowed invocation but exited 1 before writing a summary. No feature-method or hypothesis conclusion is supported.

The first auditor failure is `ValueError: focal stress yield reason mismatch` at `auditor.py:268`. Raw event `focal_shift-30072-spherical_features`, seed 30072, step 1 records candidate reason `feature shape changed`. The auditor independently detects the same focal-shape abstention but predicts reason `shape changed`. Source inspection confirms those distinct strings: `candidate.rotation_error` raises `feature shape changed`, while the auditor's `expected_image_action` raises `shape changed`. Thus the first observed mismatch is a reason-label disagreement between candidate and auditor contracts. This is a diagnosis of the first exception only; it does not validate the remaining raw rows or prove the auditor would pass after a label correction.

A03 was a new seed allocation (30060–30089 per stratum), disjoint from A01 (30000–30029) and A02 (30030–30059). A03 also corrected the prior oracle replay discrepancy, covered by a construction regression. Neither A01 nor A02 was rerun or modified. A03's first outcome is preserved as-is; do not rerun its candidate or auditor.

## Custody and verification

- Candidate and auditor source, protocol, environment, and seeds are pinned in `FREEZE.json`, frozen in commit `9fe205e86e0cc136e2b7ede76a156598395a5698` from current main `f185a9059d485a4f8d5a65e9e7f6782897f67eae`.
- Construction tests passed 13/13 in normal and optimized modes before execution. Candidate exit was 0; auditor exit was 1. Retries: 0.
- `A03-first-outcome.tar.gz` retains the candidate's complete 2,231-file / 63,489,719-byte output; SHA-256 `60d6d0ae0b04ef58c0067b17f14b053dfda0c8077350510ac7e36f7c6541a1f229`.
- Every archive member was compared against `A03-candidate-manifest.json`; all 2,231 paths, sizes, and SHA-256 values matched. A post-audit read-only comparison confirmed the expanded candidate output remained byte-identical and no `audit.json` was written.
- `A03-auditor.stderr.txt` preserves the exact traceback; auditor stdout is empty. `FORMAL_RUN.md` records both command windows, exit codes, and raw hashes.

## Scope

This is a synthetic analytic-renderer/controller experiment on local Windows CPU with CPython 3.13.14. No WSLc, container, GUI, game, model, OS input, external service, or live task effect was used. Because independent replay stopped at the first mismatch, A03 supports neither `PASS_METHOD_SCOPED` nor `H_SUPPORTED_SCOPED` and says nothing about screenshot trackers, real GUI/game control, physical release, safety, human benefit, or portability.

The first mismatch can motivate a separately frozen successor with fresh seeds and an auditor reason-contract regression. Such a successor cannot revise A03's disposition.
