# C01 parent reproduction

Run ID: `MAP01-V39-CANCEL-RELEASE-CAUSE-C01-20261004`. This one-shot host run used exact current-main `input_owner_v10.py` and the frozen two-case fake-Xlib owner-thread test.

Result: expected RED reproduced. When the controlled queue hook sets cancellation after dequeue and before `release` dispatch, the v10 owner records a verified-empty release as `release`; the ordinary-release control also reports `release`. The independent audit passes all seven checks. See `FREEZE.json`, `RED-01.stdout.txt`, `RED-01.exit.txt`, and `AUDIT-01.json`.

No retry, server, device, game, model, or formal/live allocation.
