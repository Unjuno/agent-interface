# MAP01 native Win32 recovery R182 (2026-11-14)

## Scope and frozen setup

One fresh, one-shot native trial tested automatic recovery after a producer-only abnormal exit. The frozen source was current `origin/main` at `1af9fef9e47f6a97433d50b8246ea3fcd12bc131`; frozen conditions bound custody revision 620 and the GZDoom target identity. The attempt used a new ID and conditions file. The already consumed R182 attempt was not replayed.

## Observations

- Exactly one LEFT-down dispatch was accepted; producer exited 86; automatic recovery ran once; no action replay occurred.
- Source action status stayed UNKNOWN, source release confirmation stayed false, and task success stayed null. A distinct cancellation obligation completed a returned `button_up` call (one call, one return).
- Exception-to-supervisor receipt was 282 ms, within the frozen 750 ms bound. A separate 2 s neutral horizon captured 181 samples (maximum read gap 12.2002 ms), same process identity and generation, with LEFT and W up.
- Frozen HUD oracle and separate CUA views showed ammo 50 before and 49 after. This establishes the exact HUD effect only; it does not establish task success.
- The separately measured scene region changed 305/1,003,200 pixels (0.0304027%), below its preregistered 5% threshold. General scene response therefore remains unverified.
- Bounded normal close exited 0 and did not use forced termination. Post-trial custody was clear at revision 629; the resolved operation ID and target generation match the R182 cancellation record.

## Raw custody and local checks

The private trial packet is at `private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/runner-candidates/r182-fresh-native/trials/r182_native_win32_automatic_completion_recovery_map01/`. Its 112-entry manifest includes the frozen conditions and all trial files. Every listed file's byte size and SHA-256 was re-read with zero mismatches. Manifest payload SHA-256 is `07c69fd57542b48cfbe1a59c30826432e8b74439c7d33e5ae1381ae69d6a1e5a`; manifest file SHA-256 is `eee374c6ba0bd5093f73fcc6db60cacae1fdaa565d69965dd10bf9436d0a34ea`.

The candidate's 15 offline tests pass under CPython normally and with `-O`. These are candidate regression checks, not a second live attempt.

## Limits

This is one scoped native recovery observation. It does not establish reliability, comparative latency/efficiency, or general task effectiveness. Scene-response threshold was not met. The matched comparison and token/latency/correctness report required by issue #57 remain outstanding.

## Public caller composition check

On the current main worktree, the stdio MCP integration test
`runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_stdio_exception_unknown_then_fresh_generation_recovery` passed under normal CPython and `python -O`. This test launches the real stdio MCP server/client path, queries the retained exception result through `interface_results`, preserves the source action as UNKNOWN with release unconfirmed and task success null, then calls the separate recovery tool with the observed action operation/generation and a fresh recovery generation. The synthetic recovery receipt and late-input horizon are checked. This closes the narrow caller-composition test gap for that shape; it remains synthetic and does not expand the native R182 claim.

## Expiry-path regression checks and boundary

Two current-main checks passed in normal and optimized CPython:

- `runtime.cli_v1.test_owned_win32_session.OwnedWin32SessionTests.test_expired_startup_reports_not_dispatched_only_after_gated_exit` advances the controlled clock across the lease during producer startup and proves the start gate callback is never opened. The public result is `not_dispatched` only after gated process exit/absence is verified; custody remains uncertain and replay is false.
- `runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_stdio_expiry_delayed_recovery_and_exact_call_effect` drives a real stdio MCP client/server through lease expiry, caller result polling, separate recovery, and a distinct exact-call task-effect oracle. Recovery release is confirmed and replay stays false. The task oracle returns a failed task result for the same call/operation.

The latter uses `DelayedRecoveringFakeSupervisor` and `HeldProducerFactory`; the test server assigns `program_actions_lower_bound = 2` as fixture metadata. It does not issue a late native input after expiry. Therefore the checks establish expiry fencing before the start gate and public result/recovery composition after expiry, but they do not establish that a producer already past the gate cannot emit a delayed native operation after expiry. R182 separately establishes one native producer-exit recovery and a two-second neutral horizon with no observed held LEFT/W input; it did not inject a delayed post-expiry operation.

## Next discriminating native expiry trial

The next useful native attempt should place a delayed second LEFTDOWN after the frozen action lease: first LEFTDOWN, a wait longer than the remaining lease, then a second LEFTDOWN. The owner must stop/retire the producer at expiry, separately release LEFT, and retain a two-second neutral horizon. The expected discriminators are program-action lower bound exactly one and HUD 50→49; an observed 48, unconfirmed release, wrong process/generation, failed horizon, or non-bounded recovery fails the attempt. This is a new attempt requiring a fresh unique ID, new frozen conditions, clear custody, and one-shot execution. It tests expiry during an already-started native producer; the existing R182 conditions must not be reused.


## R184 native in-flight expiry trial (2026-11-14)

A distinct R184 trial was frozen against current `origin/main` at
`1af9fef9e47f6a97433d50b8246ea3fcd12bc131`, custody revision 629, and run
once. The program moved the pointer, sent one LEFT down/up click, waited 8 s
while the authority lease expired after 3 s, then scheduled a second click.
The owner cancelled at expiry. Producer exit was `-15`; separate cancellation
returned one LEFT button-up, release was verified 31 ms after the deadline,
and its 2 s late-input horizon passed (76 samples, max gap 32 ms). A separate
post-failure neutral horizon also passed for the same process identity and
target generation (173 samples, max gap 13.62 ms). Postflight custody is clear
at revision 638, pending null, and resolves the R184 source operation/generation.
The owned game window closed normally with exit 0 and no forced termination.

The frozen candidate gate rejected this run because its SendInput threshold
was miscounted and its cancellation binding compared the cancellation
transaction's own ID with the source action ID. The public action counter is a
lower bound that includes pointer movement: one `SetCursorPos` action plus the
first click's DOWN and UP equals 3. The observed count was exactly 3 after
producer retirement; the scheduled second click would have raised it. Thus the
raw counter supports that no second click input was emitted, despite the frozen
gate file itself being false.

Passive full-client HUD classification remained ammo 50 before and after.
Therefore the intended 50→49 effect was not established and this is not a
passing task-effect trial. The CUA screenshot likewise showed ammo 50. Preserve
the run as `PARTIAL_PASS_EXPIRY_CANCELLATION_WITH_TASK_EFFECT_UNOBSERVED`; do
not relabel its frozen gate. The raw packet contains both gate failure and a
separate post-run adjudication. Its 176-entry manifest was re-read with zero
size/SHA-256 mismatches. Manifest payload SHA-256:
`9275b42d28c2b85ae779b4d896dc6156c9a282ce526b0915389293aa6828cbb8`; manifest
file SHA-256: `4b96373436178c318fcc2ea4c330e11bd18f9bfcefae695ef6851e8f107206db`.

A follow-up trial should hold the first LEFTDOWN through the expiry instead of
issuing an immediate DOWN/UP pair, then schedule the second DOWN after an 8 s
wait. Count the pointer move plus first DOWN as exactly 2; require ammo 50→49,
correct action-operation binding, recovered separate button-up, and both
neutral horizons. Freeze a new attempt ID and conditions before any retry.
**MAP01 native Win32 lease-expiry R186 (2026-11-14):** One fresh frozen-current-main public `interface_dispatch` held LEFTDOWN during an 8 s wait under a 3 s lease, with a delayed UP and second click queued after the wait. Producer exit was -15; the separate cancellation returned one LEFT button-up 15 ms after the authority deadline, and the owner verified a two-second late-input horizon (78 samples, 32 ms max gap). Independent same-process/generation neutral observation passed (183 samples, 11.78 ms max gap). The public action count lower bound was 2 (pointer move + initial DOWN), excluding the delayed UP/DOWN sequence; the source action and separate cancellation both report recovered/release-confirmed, while task_success remains null and replay is denied. R186 is **not an overall pass**: the frozen 50→49 ammo gate failed. The calibrated passive classifier returned `unknown` after recovery (score margin 0.0329 below its frozen 0.1 threshold); a separately recorded CUA screenshot visibly showed ammo 50→44, consistent with GZDoom auto-firing while LEFTDOWN remained held for the three-second lease. Treat the 44 as a visual observation, not a calibrated classifier result. GZDoom closed normally (exit 0, no forced termination), custody is clear at revision 647, and the 224-file raw packet manifest re-read with zero mismatches (SHA-256 `74c59f1a6ba5ee03c1c2b84923113c637e0581e6ab947ce195d6fc147534d316`). The packet remains local-only under `private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/runner-candidates/r186-held-leftdown-expiry/trials/r186_native_expiry_delayed_second_click_map01/`. This result isolates an important confound: holding FIRE across expiry allows repeat fire before cancellation, so a one-shot task-effect expectation is invalid for that input. Next experiment should separate release/expiry verification from auto-repeat semantics or preregister a calibrated duration-dependent ammo effect; do not reuse R186 conditions.


**MAP01 native Win32 lease-expiry R187 (2026-11-14):** A fresh exact-current-main public `interface_dispatch` made one brief LEFT tap, then held only SHIFT across a 3 s lease while the child waited 8 s; SHIFT-UP and a second click were queued after the wait. Producer exit was -15. The separate cancellation returned a LEFT button-up and SHIFT virtual-key-up, with both key-up receipts returned; source action/cancellation stayed correctly operation-bound and recovered. Public action count lower bound was exactly 4 (pointer move + LEFT DOWN/UP + SHIFT DOWN), excluding the delayed SHIFT-UP and second click. The owner verified a 2 s late-input horizon (78 samples, max gap 32 ms), and an independent same-identity/generation neutral horizon passed (see raw sample record). Release receipt arrived 16 ms after authority expiry. Frozen ammo classifier verified 50→49; CUA independently showed the same HUD values. The runner passed its scoped gates; `task_success` remains null, and this one run does not establish reliability or #57 efficiency. GZDoom exited normally (0, no forced termination), custody is clear at revision 656, and all 225 files in the raw packet manifest verified with zero mismatches (manifest SHA-256 `ed72eb367f78cc37aa8e82d12f969f1de334d191655ec58bcdf2fadb7f8eaaa0`). Local packet: `private-packets/map01_native_windows_current_main_r180_abnormal_exit_20261114/runner-candidates/r187-short-click-held-shift-expiry/trials/r187_native_expiry_delayed_second_click_map01/`. This attempt controls the R186 auto-repeat confound by separating a short effect click from the SHIFT release obligation.


**Public caller result-query regression follow-up (2026-11-14):** The exception-recovery stdio test now asserts the actual MCP SDK boundary (`isError=false`, exactly one text content item), decodes its JSON result body, and gives that body—not the SDK wrapper—to the compiled caller's `_terminal` parser. It binds the queried row to the source `call_id`, asserts the action remains UNKNOWN, and confirms incomplete bounded recovery remains `uncertain` with release unverified and no inferred `input_dispatched`. The original SDK wrapper is separately shown to fail closed. This addresses only the public result-query shape and error classification; the server/producer/recovery are synthetic and do not extend native GUI evidence. Verification on candidate HEAD `1af9fef9e47f6a97433d50b8246ea3fcd12bc131`: `python -m unittest runtime.cli_v1.test_mcp_supervised_win32 runtime.cli_v1.test_owned_win32_session` — 82 passed; same command with `python -O` — 82 passed. `git diff --check` passed. These changes were committed on the candidate branch as `35db3242417391240f38d55707179f03c3b63b6a`; they are not merged to main.

**R187 custody re-audit and current native-lane snapshot (2026-11-14):** Recomputed R187's raw `manifest-r187.json` against the packet on disk: all 225 listed files exist, all byte lengths and SHA-256 values match, there are no unlisted packet files, and there are no missing/mismatched entries. The current Windows host read-only process query found no GZDoom process. A read-only read of the current-logon durable Win32 custody journal found namespace `ad7f7502b88b793d99bdfdbcd05e2e11733e62e3e9a70faae5a7a5a890993c2b`, revision 656, `status=clear`, and `pending=null`, matching R187 postflight. This is fresh evidence for the native Windows lane at this snapshot only; it does not reserve the host against a concurrent future attempt. The WSLc shared lane remains excluded because #7924's latest available readiness record is HOLD for unknown client ownership. The next matched pair still requires unique IDs, exact frozen arm conditions and preflight immediately before the first input; no new arm was consumed in this audit.

**R188 native MAP01 repeat attempt (2026-11-14):** A distinct attempt was frozen against candidate commit `35db3242417391240f38d55707179f03c3b63b6a`; all 11 runtime-file hashes matched the R187 exact-main set. Frozen conditions used a fresh ID, the same 3 s lease / 8 s delayed SHIFT-UP + second click sequence, and the exact GZDoom/Freedoom assets. Normal and `-O` candidate gate suites passed 21/21 each; runner read-only preflight passed, with custody revision 656 clear, no pending source, no abandoned mutex, 1920×1080 display, and no pre-existing GZDoom process. The target launched at ammo 50, but a Docker Desktop WSL error modal remained foreground. The required exact-HWND/root-foreground Computer Use receipt did not arrive within the frozen 180 s; the runner recorded `action_started=false` and retained the target. No test input, recovery, or effect measurement occurred. After a targeted Computer Use Alt+F4, the GZDoom process/window was later absent; no exit code was retained, so normal close is not claimed. Postflight custody remains clear at revision 656, pending null, mutex not abandoned. This is `FAIL_PREINPUT_EXACT_WINDOW_VISIBILITY_GATE`, stays in the all-attempt denominator, and is not a technical-control success or latency sample. Private raw packet manifest: 10/10 files match size/SHA-256, no extras or missing files; manifest SHA-256 `245ca718e41815644228281d714c91a6cd3ceaa4e794b113bd82d0540092b4e7`. Do not replay R188; any follow-up requires a new ID after the Docker modal no longer obstructs the foreground gate.
