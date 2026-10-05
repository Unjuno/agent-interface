# V39 startup and release-order construction A01

## H / T / D / C / U

- **H:** The V39 `measurement_session` selector reaches V15, which selects the real telemetry release-batch backend and owner-v4/v12. In a two-key release batch, explicit key-up calls should reach the owner thread in reverse order with no intervening `query_keymap`; batch state verification should occur after both key-up injections.
- **T:** Freeze the current main commit and hash the selector, V15 wrapper, telemetry backend, typed backends, owner wrappers/owner, and fake-display harness. Verify source-level V12 default/V15 opt-in. Execute one two-key sequence through the actual V15 telemetry backend's inherited `execute/raw` methods, with only its typed command interpreter/capture superclass replaced by a deterministic seam. Record all fake XTest edges, keymap queries, sync calls, emitted per-key release receipts and final state. Independently reconstruct the inter-up operation window and verify hashes.
- **D:** PASS for this composition question only if source selector has V12 default/V15 opt-in; release rows follow SPACE then F8 with one verified owner-thread key-up receipt per row; the raw trace records all calls between key-up injections; batch verification succeeds after both; final fake physical/backend-held sets are empty; no authority grant is emitted. The query count is descriptive, with no predeclared threshold.
- **C:** Fake X plus deterministic program seam; actual selector source, V15 telemetry backend, typed-release-v2, release-batch backend, owner-v4 and runtime `research/live_control/input_owner_v12.py` execute. This runtime owner records XTest KeyRelease and XSync completion but does not provide per-key keymap occupancy samples or actuation IDs.
- **U:** No full V39 process launch, live X11/OS input, game, model, per-key physical occupancy identity, useful feedback, latency bound, recovery, threat response, or MAP01 effect.

This does not rerun the consumed A02 runner. Two earlier harness attempts used the nested A02 dependency owner's different API; their STOP is preserved separately and does not count as a production-closure result.
