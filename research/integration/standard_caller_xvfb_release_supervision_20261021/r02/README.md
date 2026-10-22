# Standard-caller Xvfb release-supervision diagnostic — r02

## Frozen run

- GitHub Actions run [39446039020](https://github.com/Unjuno/agent-interface/actions/runs/39446039020), triggered by PR #9290 at source commit `03de46502a0a982b1a6f5c29839318e8c15dcfed`.
- `.github/workflows/runtime-x11-v1.yml`, Ubuntu runner, private Xvfb. The `Run private Xvfb integration` step and all artifact uploads passed.
- This run is separate from r01's failed run 39444638512. It is one workflow and one Xvfb server lifetime, not a reliability estimate.
- The JSON and PNG artifacts are copied without editing. `SHA256SUMS` records their file hashes.

## Outcomes

All five blocked-owner cancellation cases returned a `readback_verified` independent release result and passed the independent synthetic application/keymap oracle. The two keys were up at the 8.5 s delayed-request horizon, and no late `b` press was observed. Cancel response ranged 389.790–653.976 ms; PID-qualified XRes disconnect ranged 44.886–62.445 ms; release worker elapsed 337.351–411.040 ms. In every case the public runtime remained conservative: `release_confirmed=false`, cleanup `UNKNOWN`, runtime `task_success=null`, and replay denied.

The standard-caller generation/recovery scenario passed. Stale-generation dispatch was refused. Recovery release was observed by the synthetic app and read back independently; separate synthetic property effects were `[2]` and `[3]`, with effect-commit times 35.205 ms and 30.947 ms. The runtime task-success API remained null. This is scoped Xvfb evidence, not MAP01 success.

The whole-Xvfb-stop scenario remains distinct. Cancel returned before server resume, but the original synthetic task oracle failed and the caller retained UNKNOWN/no replay. Post-resume cleanup obtained a release readback, which does not establish release during server unavailability. The run's top-level status also records its separate fresh-target recovery task result; retain this separately from the failed original task oracle.

The r01 two `worker_did_not_exit_cleanly` failures were not reproduced in this one run. Therefore r02 does not reveal what worker status those r01 failures had returned. The unit regression test verifies that a delayed child exit after sending `released` now retains that worker-reported status and timestamps while keeping the supervisor result `UNKNOWN`.

## Scope

No WSLc operation or physical desktop input was used. These results do not establish a universal blocked-platform release bound, MAP01 task success, cross-run reliability, or matched efficiency.
