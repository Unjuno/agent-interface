# V39 bounded cancellation recovery A27

## Result

`PASS_METHOD_SCOPED`. After one owner-admitted `w` key was observed as pressed, cancellation caused a same-window X11 KeyRelease and server keymap-up in **2.229 ms**, within the preregistered 2-second limit. The V12 owner recorded exactly one `owner_release(reason=cancelled)` with one verified XTest release attempt, keymap transition true-to-false, empty keys/buttons/unknown keys. The backend classified the queued per-key UP as `not_attempted_owner_cancel_release`; no explicit `owner_explicit_keyup` receipt was fabricated. Terminal release verified empty state, cleared the admission cache, the owner stopped, Xvfb exited 0, and the WSLc container was removed.

The analyzer correctly reports no complete held-time measurement: there is one admission but no explicit `input_release_transition` event for the cancellation watcher release (`unmatched_admission_count=1`). The independent X11 event and owner cleanup record establish bounded virtual key release, not a production per-key UP telemetry row. Preserving this distinction is part of the result.

## Scope

One XTEST `w` on private Xvfb using the current workspace V39 backend, current-main-frozen V4/V12 owner, WSLc 3.0.1.0 and immutable cached image `sha256:d3e433793e1b6a0bc9fb821b0aa2648945aaf7ba91c3ecc4b8b74b5123d76592`. Offline, one CPU, UID 65534, read-only sources, separate output, `--rm`. WSLc warned that host cgroup/swap limits are unsupported; no hard memory cap is claimed. No physical desktop, app/game, MAP01, model latency, visual-guard trigger, threat, navigation, survival/task effect or live allocation was exercised.

Exact source hashes are in `SOURCE_MANIFEST.json`; frozen protocol in `PREREGISTRATION.md`; raw SHA-256 `2ac94b0b86caf024849ace173fc7db43d4319097d95d45d8e0e34c4e1c63c461`; independent audit `results/a27-01/audit.json`. A26 is retained separately as a procedural STOP and was not used as preregistered evidence.
