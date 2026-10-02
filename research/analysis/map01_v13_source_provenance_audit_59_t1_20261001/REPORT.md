# Issue #59 — current-main v13 source-closure audit T1

**Disposition: `PASS_SOURCE_CLOSURE_ONLY`.** The one-shot candidate and independent raw-only auditor agreed that all 14 declared source paths match their SHA-256 pins on the frozen current-main snapshot. This T1 is a fresh additive successor to the T0 `STOP_RUNNER_REPO_ROOT`; it uses a distinct path, corrected script-derived root resolution, and a new current-main source snapshot.

It compared the exact union of the retained v13 preregistration's `source_sha256` and `canonical_upstream_sha256` maps with Git blobs at `c7346fe1ad0c0d40254c6aa7898a8ed6de76c0dc`. Result: 14 expected paths, 14 present, 14 unique pins matched, zero drift paths, zero audit errors. It did not rerun or authorize the historical `map01-measurement-integration-live-02` allocation.

The H/T/D/C/U, freeze, decision rule, and boundary are in `PLAN.md`; exact commands, deviations and dispositions are in `RUN.md`. The candidate output and independent audit are retained with `SHA256SUMS`.

## Claim boundary

`PASS_SOURCE_CLOSURE_ONLY` means only that the frozen preregistration's declared hashes match the frozen Git objects and that the independent raw audit agrees. It does not establish unlisted dependency completeness, live session behavior, release correctness, scorer isolation under runtime load, telemetry validation, MAP01 task effect, or permission to execute a fresh allocation. The historical preregistration still points to an old base and allocation; the next live gate requires a new current-main versioned source/provenance freeze and fresh explicit resource/allocation authorization.
