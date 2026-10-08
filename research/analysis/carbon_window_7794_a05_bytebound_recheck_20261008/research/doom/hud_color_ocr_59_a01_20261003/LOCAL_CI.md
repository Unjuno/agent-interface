# Local CI and publication boundary

Scientific method was frozen at intake main `38518811f537a5dc3dea3b231036b9006b25d8aa`.
Before local CI, this additive branch fast-forwarded to main
`c79f1ef958f46ff6f146edf6f3065826463ade01`. Neither study path, archived runtime,
workspace-index workflow nor deterministic replay workflow changed between
those revisions. No workflow or production source is edited by this batch.

| Check | Outcome | Retained receipt |
| --- | --- | --- |
| Current/strict workspace tests, workflow command | 22/22 PASS | `local_ci/workspace_tests.json` |
| Committed workspace namespace index | PASS, 156 roots reachable | `local_ci/workspace_index.json` |
| Prior exploratory package unit tests | 4/4 PASS | `local_ci/prior_unit.json` |
| Existing #3270 deterministic replay, bounded container | 2/2 PASS | `local_ci/replay_container_v2.json` |
| Color study saved-output closeout, bounded container | PASS evidence audit; scientific FAIL retained | `local_ci/saved_color_container.json` |
| Prior study source/frame/count audit, bounded container | PASS integrity only | `local_ci/saved_prior_container.json` |
| Saved-evidence mutations | 8/8 rejected in each phase | `CHALLENGE_pilot.json`, `CHALLENGE_evaluation.json` |

Host workspace/unit checks use bundled Python 3.12.14. The bounded container checks
use the same frozen Python 3.12.3/Pillow/Tesseract image as the experiment.
Workspace tests require local Git, absent from the OCR image. No remote CI
dispatch, OCR replay, live GUI/model/input, or other worker allocation is used.
Commands, full stdout/stderr, exit codes and durations are in receipts.

## First CI harness failure, preserved

`local_ci/replay_container.json` exited 1 because an absolute `/test_replay.py`
unittest module argument resolved to the invalid module `/test_replay`. It did
not run either replay test or any scientific OCR. The corrected invocation
mounts the same source under `/tests`, sets the workdir there, and invokes module
`test_replay`. It uses a distinct container and receipt; the failed record is
unchanged. This is a test-launch repair, not a scientific rerun.

## Runtime closeout

`local_ci/terminal_inventory.json` inspects the exact four scientific and four
CI containers on the private Docker daemon. All eight are terminal and carry
this study's owner label. Only the first CI launch exited 1; the other seven
exited 0. `setup/owned_vm_stop.json` records successful stop of the owned VM.
The VM/image/containers are retained recoverably; no other VM was stopped.

## Remote checks still apply

Current automatic workflow inventory was inspected before publication. A
focused PR may run the existing deterministic #3270 replay and workspace index
checks. The #4242 formal job is guarded to a different branch. Study-specific
live/formal workflows are not triggered by these additive paths. No workflow
is added or changed to re-run this experiment remotely. Check the actual PR
head and check conclusions before merging; local PASS is not remote PASS.

The top-level `SHA256SUMS` covers both additive study packages except itself.
Use the following from the repository root for a saved-only custody check:

```sh
shasum -a 256 -c research/doom/hud_color_ocr_59_a01_20261003/SHA256SUMS
```
