# Issue #59 Linux-container replay: DOWN acknowledgement loss

## H / T / D / C / U

**H.** At candidate source `e00132595e0e801aabeae97ada53c580dfb11b9d`, the delivered-DOWN/failed-`sync()` regression and related owner measurement tests remain reproducible in the repository's pinned Python 3.12 Linux container. The scoped outcome is a `KEYMAP_EDGE_UNCONFIRMED` measurement with no bracket or actuation identity, followed by verified cleanup to a neutral fake-X state.

**T.** Build one image from the pinned Python base digest in `Dockerfile`, install only the exact packages in `requirements.lock`, and run `test_batch_key_measurement_composition` once. Mount source read-only and a new output directory read-write. The container gets one CPU, 1 GiB memory, 64 pids, no network, no host display, no game, and no GPU. Run the saved-data auditor once after the container exits. No retry is permitted for build, run, or audit.

**D.** PASS only if all 11 focused batch-composition tests pass and the raw-only auditor confirms the delivered keycode 38 is observed down before cleanup, the emitted input-attempt measurement is explicitly unconfirmed with null bracket/actuation ID, cleanup is verified, and the final fake-X key set is empty. A container/build/import/runner failure is STOP. Any predicate failure after test execution is FAIL. Preserve the first outcome.

**C.** The test injects the exception at the caller-visible `sync()` boundary after the fake server applies DOWN. Test or auditor errors could obscure behavior; source and harness digests are checked independently. The test double may not reproduce X server scheduling or transport failure.

**U.** This is Linux/Python dependency reproducibility over fake-X state only. It proves no real X11 server behavior, physical keyboard state, GUI/application effect, threat response, recovery efficacy, Doom progress, or live #59 gate completion. Docker build may need registry access; runtime networking is disabled.

## Frozen identities and command

- Candidate source commit: `e00132595e0e801aabeae97ada53c580dfb11b9d`.
- Base image: `python@sha256:dddfd7e07f9d15aeeca61529320492139d21cac7f0070c00609243e51e4e0016`, previously used by the repository's #59 container construction package; this experiment does not invoke that package's launcher.
- Focused suite: `research/live_control/test_batch_key_measurement_composition.py`.
- Output: `results/a01/`, new and empty before execution.
- The exact build/run commands and resulting image/runtime identities are recorded in `results/a01/COMMANDS.txt` and manifests.

Build once with the OrbStack-managed Docker CLI, then run once with `--network none`, read-only root/source, and only `/out` writable. If the engine returns the known containerd blob error, retain it as STOP and do not reset, prune, or retry the shared engine.
