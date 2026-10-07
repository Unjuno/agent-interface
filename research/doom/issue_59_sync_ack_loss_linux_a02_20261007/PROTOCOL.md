# Issue #59 Linux-container replay: DOWN acknowledgement loss (A02)

A02 is a new frozen successor to A01. A01 remains preserved as `FAIL_TESTS`; it is never rerun or overwritten. A02 fixes the missing Python repository root and adds read-only mounts for only the two imported research namespaces (`observation_tiles` and `observation_gating`). The runner adds `/workspace` to `sys.path`. The auditor uses missing-row-safe access so an unexpected runner failure produces a saved FAIL audit instead of crashing.

## H / T / D / C / U

**H.** At candidate source `4cfc5db38bc2a088b8c5901ffe1d8817ab85f099`, the delivered-DOWN/failed-`sync()` regression and related owner measurement tests remain reproducible in the repository's pinned Python 3.12 Linux container. The scoped outcome is `KEYMAP_EDGE_UNCONFIRMED`, with no bracket or actuation identity, followed by verified cleanup to a neutral fake-X state.

**T.** Build one image from the pinned Python base digest, install exact dependencies from `requirements.lock`, then run the 11 focused tests once. Mount required source trees read-only, output read-write. Runtime gets one CPU, 1 GiB memory, 64 pids, no network, display, game, or GPU. Run the saved-data auditor once. No build, run, or audit retry.

**D.** PASS requires all 11 tests to pass and the auditor to confirm keycode 38 down before cleanup, an explicitly unconfirmed measurement with null bracket and actuation ID, verified cleanup, and an empty final fake-X key set. A build/import/runner error is STOP; any failed predicate after test execution is FAIL. Preserve the first outcome.

**C.** The exception is injected at caller-visible `sync()` after the fake server applies DOWN. Test or audit errors could obscure behavior; source and harness digests are checked independently. The fake does not reproduce X server scheduling or transport failure.

**U.** This validates Linux/Python dependency reproducibility over fake-X state only. It proves no real X11, physical keyboard, GUI/application effect, threat response, recovery efficacy, Doom progress, or live #59 gate completion.

Candidate source commit: `4cfc5db38bc2a088b8c5901ffe1d8817ab85f099`. Base image digest: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`. Result directory: `results/a02/`.
