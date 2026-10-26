# Win32 current-main blocked-producer recovery and fresh-generation task R35

**Result: `PASS_RECOVERY_FRESH_GENERATION_TASK`, one scoped Windows synthetic-fixture sample.** Frozen source main: `b0092967e84b65c9f63ba146709330f776a5efa9` (runtime tree unchanged). The end-to-end additive audit passed all 15 checks; it verified all 4 frozen-input hashes and all 38 raw-run hashes.

## Experiment

The first fixture (PID 60328; generation `6cfe21f17b49330dc267007bb488da8ca73d41261089e933a6b67b8a0e247466`) was brought to the foreground through CUA and passed independent native preflight. The producer-local SHIFT-up callable was held before it invoked native `SendInput`, after the operation had sent SHIFT down. One public `interface_cancel` returned `pending` in **0.366 ms**, with replay denied and release still unconfirmed in that immediate response. Supervised recovery retired the blocked producer, sent release from the separate recovery path, and completed in **17.0471 ms**, within the 3 s cleanup deadline. The same-generation independent native readback confirmed SHIFT up. The first fixture exited with code 0.

The old generation was then refused with `TARGET_GENERATION_CHANGED` and `input_dispatched=false`. A distinct fixture PID/generation ran exactly one public compiled task through the standard caller. The fixture event journal recorded one click, the six characters `office`, and save. The separate `interface_verify_task` oracle returned `verified / task_success=true` for the exact action call `693da64e883845ab9f61038b62cafc10`, operation `99ec945839344744b7f0039ef1cfb779`, generation `1938653700ceab7ead577ca7e99b97281e634b1267a21ffb0b83f7ba791a7ca7`. Independent same-generation readback found SHIFT, CTRL, S and the left mouse button up. The task fixture exited 0 and the original foreground window was restored.

The canceled recovery call itself correctly remained `task_success=null`; the later task's separate oracle receipt is the evidence for its effect. The two outcomes are not conflated.

## Preserved setup outcomes

R31–R34 are retained as predispatch/setup failures and were not retried under their original attempt IDs: R31 refused an orchestrator-precreated empty output directory; R32 found a nonforeground fixture and `UNKNOWN` input state and sent no input; R33's static audit syntax check failed before runner launch; R34 had a `user32` DLL-name typo and launched no fixture. Each failure led to a new attempt identity; none sent input to GZDoom or the user desktop.

## Limits and custody

This proves bounded recovery for one controlled producer-local stall **before** native `SendInput`; it does not prove release through an operating-system/kernel hang, an arbitrary I/O bound, a reliability rate, MAP01 success, production-app correctness, or an efficiency advantage. No WSLc, Docker, model or provider was used.

The raw packet, frozen scripts/conditions, receipts, independent audit and hash manifests are retained locally at `C:\Users\user\Documents\Codex\2026-10-03\new-chat-2\private-packets\win32_native_sendinput_recovery_20261026_r31_r35` under `PACKET_MANIFEST_R31_R35.json` (SHA-256 `3bfdd3e277d1ba043a963e7ee1acae2bac49d80e93a1583ac331f6c6425fb555`; 91 evidence files). The summary copy is `RESULT_SUMMARY.md`. R31–R35 execution folders are excluded locally from Git; this result page is the reviewable repository summary.