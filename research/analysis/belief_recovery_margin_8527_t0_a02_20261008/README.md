# Issue #8527 — belief-space recovery margin T0 A02

This package is a new finite-method allocation following the preserved #8527 A01 construction/runner STOP. It asks whether bounded belief-set safe-reachability finds a common observation-contingent recovery policy—not merely separate per-state routes—before a finite control budget expires.

## Current status

Construction only. Windows CPython 3.12.10 construction suite: 10/10 passed normally and 10/10 under optimized Python. Formal candidate: not run. Formal auditor: not run. No WSLc call is part of this construction step. The shared WSLc exclusive-lane gate is still being clarified; the source freeze and result remain pending.

No GUI, model, user, game, network, runtime control, calibrated probability, real-time deadline, or product claim.

## Files

- PROTOCOL.md — H/T/D/C/U, case map, sealed decision rule and run gates.
- input.json — finite model visible to the candidate.
- truth.json — sealed row-wise status, minimum-step and margin expectations.
- candidate.py — bounded policy-search candidate; never reads the truth oracle.
- audit.py — exhaustive policy-tree auditor; does not import the candidate.
- test_solver.py, test_audit.py — construction and mutation tests.
- CONSTRUCTION_LOG.md — first implementation/test history.
- FREEZE.json, SHA256SUMS — to be completed against current main before any formal invocation.

The 10 × 4 corpus covers seven fully specified cases and four incomplete/stale/unverified cases (with late-cue reusing a one-step cap at larger displayed horizons). The information-gathering case needs two actions and succeeds exactly at budget 2. In the aliased case, each singleton state has a safe recovery action, but the joint belief has no single safe action.

Formal execution, if authorized, is a single candidate run followed by one separate independent audit in WSLc with a pinned cached Python image, no network, read-only input mounts, and separate exclusive output. The issue-specific shared WSLc ownership gate must be explicitly cleared before any such invocation.
