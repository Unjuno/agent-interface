# Idle observation recovery: three fixture failures

Three fresh, separately frozen WSLc private-Xvfb attempts tried to extend the [observed stopped-server cell](../wslc_idle_observation_stop_verified_20261101) with a fresh session sending a key to a separate synthetic X client after the old reader timed out. **None achieved the intended recovery/task-effect criterion.** No held input or MAP01 scenario was tested.

| Allocation | Failure | Evidence |
|---|---|---|
| a03 | Invalid hyphenated target alias | The old read timed out while Xvfb was stopped and the old worker exited after resume, but mint rejected `fresh-field` before keyboard input. |
| a04 | Flat visual target | The alias was corrected to `fresh_field`; the same guard refused the uniform target region before keyboard input. |
| a05 | Fixture event-handler error | A contrast marker was added, but the target used nonexistent `X.Exposure` rather than `X.Expose`, exited with an exception, and the initial capture failed with `BadDrawable`. The stop/recovery sequence was not reached. |

The `a03` and `a04` old owners remained at observation sequence 1, required review, and their retired workers exited after server resume; these facts do not establish that the subsequent task succeeded. Each archive records the exact candidate, frozen conditions, output and failure. All three launchers exited 1 and their private X servers exited zero. The target exited zero in a03/a04 and one in a05. There is no target key-event result in any archive. No failed attempt is counted as a successful recovery.

The next candidate needs an independently exercised target preflight: keep the target alive through an Expose event, verify the marker is visible and textured at the intended crop, and demonstrate a key press/release changes the target's value before consuming a new recovery trial. Correcting the fixture is preferable to weakening visual admission. The bounded idle-observation implementation remains an unmerged prototype.

`a03.zip`, `a04.zip` and `a05.zip` retain frozen source hashes, conditions, receipts, stderr and results. Run `python research/integration/wslc_idle_recovery_fixture_failures_20261101/audit.py` without `-O` to verify archive manifests and the recorded failure boundaries. The audit checks saved evidence rather than independently reconstructing the historical X events.
