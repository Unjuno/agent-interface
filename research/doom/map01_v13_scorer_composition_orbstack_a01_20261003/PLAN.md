# Issue #59 — v13 scorer composition OrbStack A01

## H / T / D / C / U

- **H:** the current-main MAP01 v13 scorer-only composition passes its retained synthetic episode/thread/provenance contract in the pinned OrbStack container.
- **T:** run `test_session_map01_v13.py` exactly once with explicit Python entrypoint, network disabled, source mounted read-only, 1 CPU / 1 GiB, and bounded tmpfs. The test drives a fake game and a separate pipe writer; no real game action or input is sent.
- **D:** PASS_CONSTRUCTION_SCOPED only on exit 0 and all assertions passing; otherwise retain first failure without retry.
- **C:** Python/platform or thread/pipe scheduling in the container can expose a contract defect.
- **U:** this cannot establish real X11/ViZDoom integration, release telemetry, scorer timing during a real episode, useful task progress, model-wait recovery, threat exposure, or MAP01 completion.

The predecessor command-shape STOP is preserved in `FREEZE.json`; it never reached the test. This is a fresh, separately frozen construction allocation, not the R134 live allocation and not authorization for a recovery comparison.
