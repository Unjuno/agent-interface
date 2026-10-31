# Overlay control for MAP01 visual change review

This is a negative semantic control for #9894's screenshot crop comparison. Four fresh network-none WSLc containers used private Xvfb, Freedoom2 MAP01 ASYNC_SPECTATOR at 35 tics/s, skill 1, seed 991031, one CPU, 1 GiB and image sha256:6150a4f3c779a51b3ac6a7d93bc1d0450803325efb7ab38ade8b1aaf79c33e25. The same script ran wait/overlay/overlay/wait. No game input was dispatched. In the overlay runs, a separate X11 child window placed an 8x8 magenta block inside the previously selected HUD crop after the baseline capture and before the bounded visual review; it was removed afterward. Control runs made no overlay. Game-engine ammo was evaluation-only and never used by the review decision.

| Run | Condition | Review result | Checks | Evaluator ammo |
| --- | --- | --- | ---: | --- |
| u01 | wait | timeout_unknown | 9 | 50 → 50 |
| u02 | overlay | visual_change_observed | 1 | 50 → 50 |
| u03 | overlay | visual_change_observed | 1 | 50 → 50 |
| u04 | wait | timeout_unknown | 9 | 50 → 50 |

The change detector correctly reported that its pixels changed, but the injected unrelated display change shows why interpreting that signal as ammo consumption, action success, or a recovery decision would be wrong. The existing output correctly keeps semantic effect unknown and dispatches no review input. This control does not measure the frequency of real-world obstructions, prove that other signals are unreliable, or establish any general false-positive rate. The overlay was deliberately synthetic and chosen to overlap the crop; these tests do not include an attack, cancellation, model call, or completed task. The 500 ms deadline is cooperative, not a bound on blocked capture or total wall time.

The four ZIPs retain all screenshots, raw telemetry, source, receipts, overlay times and output. `python audit.py` verifies crop hashes, the magenta pixel, observation order, unchanged ammo, no-input receipts and timeout controls. The mounted runtime Python matches main 6a9c787d2caf9740612de65bd2539846dd87cad4 as recorded in #9891; main through 754588e55353dec21f8cb60ef7c7b27ad4c81c0c adds research records only. No product code changed.
