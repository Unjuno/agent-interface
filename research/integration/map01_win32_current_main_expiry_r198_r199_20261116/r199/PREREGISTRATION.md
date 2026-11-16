# R199 preregistration — 2026-11-16

- Attempt: `map01-native-expiry-delayed-input-r199-20261116`
- Source: current main `86a52662dc2bb690dd670d52ea8d97816aef2a26`; tree `c35b16d1df4f2e7c6b70a09e2ec672043ace5335`; 11 runtime files hash-pinned.
- Conditions SHA-256: `a692285d1a4077e6db4e16198d0a40b5e20cfb670fbe85e2732291322b02885a`
- Independent attempt: one fresh native MAP01 run with unique output `r199_native_expiry_delayed_second_click_map01`. R198 is preserved and will not be replayed.
- Fault: one accepted LEFTDOWN with bounded 120 ms dwell and LEFTUP, then SHIFT held across 3 s lease expiry; delayed SHIFTUP and second click are queued after the 8 s wait. Producer exits abnormally without backend cleanup.
- Frozen source projection: ecovered and release confirmed 	rue only when current-main cancellation, operation ID, target generation, recovered phase/status, and release proof match. Otherwise it remains unknown/unconfirmed. Cancellation is separately recovered/release-confirmed. Outer dispatch reports input_dispatched=false. 	ask_success=null in all outcomes.
- Required evidence: one dispatch, at most one recovery, delayed operations excluded, native LEFT button-up count 1, SHIFT release, recovery latency within 1 s, integrated 2 s late-input horizon and independent 2 s neutral horizon, pistol-gated ammo HUD 50 to 49, bounded normal process close, custody clear afterward. Any mismatch fails the attempt.
- No replay. If target/HUD/foreground/process identity or custody gates fail, do not dispatch input. Preserve all raw results from the one attempt.
- This validates one scoped effect/recovery path. It does not measure integrated model/provider tokens, cold/warm/invalidation/repair lifecycle, or comparative cost.
