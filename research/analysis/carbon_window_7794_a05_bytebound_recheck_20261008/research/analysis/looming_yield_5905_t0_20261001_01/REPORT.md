# Issue #5905 T0 — rendered looming cue (executed)

**Allocation disposition: `STOP_MAIN_ADVANCED_AFTER_FREEZE`; preregistered scientific disposition: `NOT_EVALUATED`.** The candidate and auditor did execute, and their raw results are retained below as a descriptive run with a start-gate deviation. Do not promote the auditor's data-replay PASS to an allocation-level METHOD PASS. This is not a GUI, DOOM, safety, or product result.

## Result

The candidate ran once in a network-disabled Docker container on a separately created OrbStack Ubuntu 24.04 ARM64 guest. A separately implemented raw-only auditor ran once in a second container using the same pinned image digest. Both exited 0; retry count was zero. After execution, a commit-history audit found main commit `8afb359a4052d0b242337965378b5917338b3267` was created at 08:20:30 UTC, before candidate start at 08:24:29 UTC, advancing main past the frozen base. The mandatory immediate pre-candidate refetch was missed. This violated the preregistered exact-main launch gate; allocation status is therefore STOP and scientific disposition NOT_EVALUATED, while preserving the observed raw and audit unchanged.

- 11 cases total: 4 eligible centered constant-speed approaches and 7 declared assumption-boundary controls.
- 144 losslessly retained PGM frames, including per-frame timestamp, source/track identity, and SHA-256.
- All 4/4 eligible approaches requested simulated release before analytic contact. Independent TTC absolute error at the decision frame ranged 0.09246–0.09940 s (gate ≤0.20 s); simulated release lead before contact ranged 1.7–1.8 s.
- All 7/7 controls returned `UNKNOWN`, `safe=false`, and no release request: lateral passage, camera zoom, animated growth, occlusion, track swap, timestamp regression, and a visible nonlooming hazard.
- Independent raw-data audit: `PASS_METHOD_SCOPED`, errors `[]`; it recomputed frame digests/shapes, rendered geometry, schedule, raster-area TTC, contact/release clocks, identity, and control disposition directly from fixture plus raw. This validates internal replay only, not the failed launch gate.

## Important interpretation boundary

The eligible TTC estimate is measured from rendered image pixels, but the boundary-control observability fields (e.g. camera-scale change, occlusion, target rigidity, and hazard presence) are supplied by the synthetic fixture. This run therefore tests a raster-expansion cue plus fail-closed consumption of already-observable metadata; it does **not** implement or validate visual detection of those conditions. No endpoint-only/pixel-change matched-false-stop comparator was run, and no task progress or effect endpoint was measured. A subsequent method rung should test whether those assumption signals can themselves be extracted from images and compare simpler cues at matched false-stop allowance before any live-control claim.

## Reproduction and provenance

Allocation, exact commands, source/image hashes, container IDs/limits, guest identity, and execution times are recorded in `FREEZE.json` and `RUN.json`. Full frame bytes and labels are in `raw.json`; machine audit receipt is `audit.json`. `SHA256SUMS` covers the retained inputs and outputs. The source preregistration was frozen on main `430e6b3aeedb34ac2b1bf808def5445482f31948` before the candidate invocation.

Host construction CI after the final main rebase: 3/3 unit tests, `py_compile`, `git diff --check`, and the generated analysis index passed. Candidate and auditor results come only from the described containers; host checks did not execute either formal command.
