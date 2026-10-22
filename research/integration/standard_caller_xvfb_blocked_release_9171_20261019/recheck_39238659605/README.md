# Standard caller blocked-Xvfb recheck — 2026-10-19

This additive packet preserves the exact failing CI outcome and two local WSL outcomes for the same synthetic standard-MCP/private-Xvfb scenario. Raw files are immutable; corrections or later results belong in new run directories.

## CI failure and diagnosis

GitHub Actions run [39238659605](https://github.com/Unjuno/agent-interface/actions/runs/39238659605) tested PR [#9171](https://github.com/Unjuno/agent-interface/pull/9171), PR head `9dfa23c0618bc00c867b808dff34ca7eb40d0530`; the workflow artifact records merge source `0e25e0d404260628e3a4c347995e3da0049c45d0`. The exact outcome is `FAIL_CLEANUP`.

The standard caller returned from cancel in 698.63 ms, retired the exact owner, observed XRes disconnect for the matching resource base, and completed a separate release worker with empty key/button readback in 616.60 ms. A separate parent readback showed `a` and `b` up, and `b` was not observed during the 8.5 s horizon. The caller correctly retained `release_confirmed=false`, `cleanup_status=UNKNOWN`, `task_success=null`, and `replay_allowed=false`. The failure occurred during final `interface_close`: close tried the already-retired owner again and cleanup returned `cleanup_failed`, triggering duplicate cleanup work. This is a cleanup-idempotence defect, not a positive task-effect or release guarantee.

## Local WSL outcomes

Both local runs used a synthetic application, private Xvfb, and the standard MCP caller with the same bounded scenario. The Windows Python environment was 3.11.9 with pinned `mcp==1.30.0` and `python-xlib==0.33`; Xvfb and its helper tools ran in WSL Ubuntu. These were local synthetic checks, not a newly allocated WSLc experiment, real user application, or MAP01 task.

- **WSL `/mnt/c` — `FAIL` / filesystem-specific STOP.** The disconnect observer exceeded its 150 ms supervision limit (153.26 ms); owner retirement was observed, but disconnect stayed unknown and release was not attempted. Do not repeat this exact mount condition as a success trial.
- **WSL ext4 — `OBSERVED_SCOPED_XVFB_STANDARD_CALLER_CANCEL_CLEANUP_UNKNOWN`.** Cancel returned in 330.36 ms; XRes confirmed exact-owner disconnect in 38.11 ms; the separate release readback verified keys/buttons up in 289.94 ms. Independent parent and horizon readbacks showed `a` and `b` up, with no late `b` in the 8.5 s horizon. Terminal remained `runtime_failed`; close returned `cleanup_failed` while preserving the same release-attempt evidence, `release_confirmed=false`, `cleanup_status=UNKNOWN`, null task success and replay denied. This does not qualify the task as successful.

The mount comparison indicates a meaningful filesystem/supervision boundary for this fixture, but the two single local runs do not establish a general causal or cross-platform performance result.

## Local verification of the close-idempotence repair

On Windows Python 3.11.9, the focused owned-process module passed 23/23 tests in normal and optimized (`-O`) mode; the targeted regression and three related retirement/close tests passed. The complete `runtime/cli_v1` discovery passed 467 tests with 7 skipped in both normal and optimized mode. The exact commands were `python -m unittest discover -s runtime/cli_v1 -t . -p 'test_*.py' -q` and `python -O -m unittest discover -s runtime/cli_v1 -t . -p 'test_*.py' -q`, from the repository root with the pinned environment and `PYTHONPATH` set to the repository root and `runtime/cli_v1`. The private-Xvfb ext4 integration test also passed with the fail-closed cleanup receipt described above.

## Source and artifact integrity

CI raw JSON and its observation PNG, plus both local JSON outcomes, are preserved byte-for-byte under `raw/`; hashes are listed in [SHA256SUMS](SHA256SUMS).

Local source file hashes bind the WSL outcomes to the edited tree based on PR head `9dfa23c0618bc00c867b808dff34ca7eb40d0530`:

- `runtime/cli_v1/owned_guarded_session.py`: 62388cb052dea1370c9c92c40c8a1aca8c54502175f9c39a596ed8b81210d42c
- `runtime/cli_v1/test_mcp_owned_process.py`: 3fbac0fa51597f4aed44d1b4931a5ec397bde5c30a7088bac46ca510319c584d
- `runtime/cli_v1/test_mcp_xvfb_blocked_release_integration.py`: a7123def3d1fed8cdd9558354856d698f41563ab267dc7154797653f4e9d9812

This packet retains a failed CI result, a filesystem-specific STOP, and one scoped synthetic observation. It does not establish physical input release, live application effect, finite task recovery, efficiency improvement, or MAP01 completion. Keep Issue #17 open and all release/task conclusions UNKNOWN. Any future live trial requires a separately verified unused allocation and fresh custody check.
