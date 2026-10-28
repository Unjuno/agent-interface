# Persistent global auto-repeat OFF caller control

## Conditions and outcome

The three standard-caller attempts used the same pinned Docker image, exact main-source hashes for the cancellation harness and runtime files, private Xvfb `:88`, 4,000 ms server pause, 8,000 ms delayed B XTEST request, prestarted cancellation supervisor, and test-only 12 s transaction window.

- R01 set global repeat OFF and read back 0, then exited the setter process before the caller test. It had no in-run mode sampler. The task effect count was 7 vs expected 1, but mode during the run is unknown.
- R02 used the same short-lived setter lifecycle and added a passive sampler. All 1,147 in-run mode samples read 1; the nearest samples to three extra A KeyPress events also read 1. The setter's mode change did not persist after its process exited. Task effect count was 4 vs expected 1; old-task oracle failed.
- R03 kept the configuring X client connected while sampling global mode and A key state every 5 ms. All 1,039 samples read mode 0; the app trace contained one A KeyPress total and exact effect count 1. The old-task oracle passed. The monitor's maximum gap was 4,002.561 ms while Xvfb was paused, so the server could not be sampled during that outage.

## Other gates

Across these attempts, the owner retired, disconnect was observed, the prestarted supervisor reported release readback verified, separate A/B release readback passed, delayed B was not observed at the 8.5 s horizon, and a distinct fresh-generation C task passed. R03 ended with all keys up. However, the canceled old API call still reports `release_confirmed=false`, cleanup `UNKNOWN`, `task_success=null`, replay denied, and terminal `runtime_failed`. These receipts do not upgrade the runtime contract.

The persistent-OFF result supports active Xvfb global repeat as a contributor to the synthetic duplicate-A pattern. It is one sample per condition, with the pause-time observation gap and no counterbalanced repetition. The original R02 full structured raw was overwritten and is unavailable, so exact historical causality remains unproven. This is not a production change, native Win32/WSLc/MAP01 evidence, broad reliability, or efficiency comparison.

Full local packets:

- `private-packets/docker_xvfb_delayed_release_txn12000_autorepeat_off_currentmain_20261029_r01`
- `private-packets/docker_xvfb_delayed_release_txn12000_autorepeat_off_monitor_currentmain_20261029_r02`
- `private-packets/docker_xvfb_delayed_release_txn12000_autorepeat_off_persistent_monitor_currentmain_20261029_r03`
