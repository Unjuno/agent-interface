# Prestarted XRes target identity: R115 failure and R116 follow-up

R115 was a single frozen public MCP Xvfb cell. It failed before mint or input: first observe returned `runtime_failed`, `target_identity_unavailable`. The retained raw packet is [raw/r115](raw/r115); it was not retried. The receipt did not expose the inner reason, so its exact failure cause is inferred, not directly observed.

The parent creates the one-shot identity supervisor using its initial session ID, then the child owner returns a different session ID and `_apply_snapshot` replaces the parent ID. A focused regression reproduced this mismatch (red: parent-session versus child-session). The fix does not pre-bind the worker to the provisional parent ID; the supervisor continues to require the worker receipt to match the actual request operation and child session IDs. The focused test and 19 other target/owner tests passed in the pinned Linux image.

R116 is a new, separately frozen one-cell follow-up, with the change and an explicit receipt gate declared before execution. Docker exit 0; result PASS, 15/15 gates. With a 650 ms Xvfb stop and an 8 s delayed request, the owned old target was retired before resume, old result remained UNKNOWN with no replay, the runtime release had readback, and the distinct fresh target received B exactly once and no old A through the 8.5 s observation horizon. The target identity receipt matched the child session and the identity worker exited cleanly. Server creation was 528.39 ms and first observation after creation 1165.32 ms in this one cell; these are not a paired speed comparison. Raw, source hashes, preregistration, runner and post-trial checksums are in [raw/r116](raw/r116). These artifacts came from the private synthetic Xvfb environment; the original local packets are also preserved.

This is an experimental opt-in overlay on main d534, not a merged feature. It does not establish general reliability, WSLc or MAP01 success, or end-to-end agent speed. The R115 diagnosis remains an inference because its nested rejection was not retained.

## Follow-up regression: stopped server

On 2026-10-30 the opt-in private-Xvfb regression was extended to construct the prestarted identity worker while the server was healthy, stop that exact Xvfb, and request binding with a 200 ms transaction deadline. It requires `target_identity_unavailable`, `transaction_deadline`, confirmed worker retirement and return within 1 s while the server remains stopped. The same test retains the fresh-worker timeout and bound-target retirement checks, with a resume watchdog and explicit cleanup. In the pinned Docker image with network disabled, read-only root and source, and `AGENT_INTERFACE_OWNED_TARGET_XVFB_TEST=1`, the Xvfb and related target/session suites passed 20 tests in 0.895 s. This is a regression check, not a new formal reliability allocation or a task-level benchmark.

## Independent regression reproduction

Use a new, empty output directory; do not write into `raw/r115` or `raw/r116` or call a later run either historical allocation. From this repository root on a Linux host with Docker and the pinned image available locally, the following runs the preserved R116 runner as a new local regression (the image is not pulled by this command):

```sh
mkdir -p /tmp/owned-target-regression-new
docker run --rm --pull=never --network none --read-only --tmpfs /tmp:rw,nosuid,nodev,size=128m \
  --mount type=bind,source="$PWD",target=/workspace,readonly \
  --mount type=bind,source=/tmp/owned-target-regression-new,target=/evidence \
  --workdir /workspace -e TARGET_RETIRE_MODE=retire \
  sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425 \
  python3 -B /workspace/research/integration/docker_xvfb_prestarted_target_binding_r116_20261030/raw/r116/pilot.py
```

Read `/tmp/owned-target-regression-new/result.json` and inspect the individual checks and cleanup. The runner creates private Xvfb and disposable child processes inside the isolated container. Startup, timing and scheduling vary by host. It is not a matched performance comparison and a later run does not replace the frozen historical results. The `raw/.gitattributes` rule preserves the exact bytes covered by the recorded checksums.

The source manifest hashes the bytes actually mounted during R116. Eight tracked baseline/overlay Python files were checked out with CRLF line endings on the Windows host; their Git blobs use LF and therefore hash differently. Converting the corresponding Git blob LF line endings to CRLF reproduces each of those eight manifest hashes. The two newly added Python source files in the manifest match their Git blobs directly at PR commit `38715d930a15f43c926e350cc049fad38ec2e494`; `owned_target_session.py` changed later to recheck an unconfirmed retirement on explicit close, so the current file no longer has the R116 hash. The preserved runner hash is checked against `raw/r116/pilot.py`. This reproduction command exercises the same code with the checkout's line endings; it is not a byte-identical replay unless the listed hashes are matched first.

## Post-R116 cleanup regression

The first candidate cached an UNKNOWN target-retirement receipt permanently. If independent input release had been readback-verified, the base close path reused the release receipt and never called target cleanup again. A focused mocked regression reproduced the missing target recheck. The later patch allows one bounded target retirement attempt on each explicit later close when the previous attempt is UNKNOWN and the control owner is confirmed retired; it retains the previous receipt and does not change old task UNKNOWN or allow replay. It does not retry a refused identity or operate while owner retirement remains unconfirmed. With that patch, the pinned Docker image passed 84 target, Xvfb, existing MCP-owner and cancellation-supervisor tests. This is local regression evidence, not a repeat of R116 and not an application-level effect proof.

A later Linux regression injects a pidfd signal error for a real disposable child, then calls the experimental session close and verifies that the same pidfd retires that child while an unrelated witness child remains alive. A private Xvfb variant additionally binds the actual XRes window to the child before stopping Xvfb; while it remains stopped, it injects the first signal failure and verifies a successful bounded recheck and retained UNKNOWN/no replay. Both tests mock the base close report/control-owner retirement, and the witness test mocks XRes identity, so neither demonstrates full public MCP fault recovery or real application effects. The target/session/Xvfb suites passed 24 tests in the pinned Docker image (0.676 s).

## R118: public MCP injected retirement failure

R118 is a separately frozen, one-cell, no-retry experiment against PR source 24ab4707719c22469161df733cbb925b594539d6, with a single injected `PermissionError` on the owned target pidfd signal. See [raw/r118](raw/r118) for the runner, preregistration, source hashes, output and checksums. Its 16 predeclared gates passed: cancel recorded the initial target exit as UNKNOWN with `pidfd_signal_failed`; the exact old target was alive before Xvfb resumed; explicit public close then confirmed target retirement while retaining the failed receipt; the old call and close remained UNKNOWN with replay denied; runtime release had readback; and the fresh target recorded B once and no old A through an 8.5 s horizon. The Xvfb stop lasted 651.15 ms.

**Counterevidence:** the old target recorded one A press before the stop and three A presses by its final recorded state. The additional two press events occurred approximately 4.5 ms and 43.3 ms after Xvfb resumed, while the old target was still alive; a release readback occurred between the two. The trial had autorepeat enabled, and this data does not identify whether the additional presses were autorepeat or queued input. Thus the PASS applies only to the preregistered recheck and fresh-target gates; it is not a pass for preventing extra old-target effects. Keeping the target alive until explicit close leaves a consequential exposure window. The historical runner's `old_process_retired` timing field is misleading in this cell: it records a checkpoint before resume while the target was alive, not retirement; use `alive_before_resume`, `exitcode_after_close`, and the target receipts instead.

## R119: one repeat-off / repeat-on comparison

R119 predeclared two new cells, OFF followed by ON, each with the R118 one-time pidfd failure injection; no retries. Source, runner, raw outputs and preregistration are in [raw/r119](raw/r119). Both cells passed all 16 recheck and fresh-target gates. In the OFF cell, old A presses remained 1 before stop and 1 at the end; in the ON cell, they increased from 1 to 3. Xvfb stops were 651.09 and 651.29 ms respectively. Both fresh targets recorded B once and passed the horizon/release gates. This one fixed-order pair meets the preregistered criterion for limited support that autorepeat contributes to the additional old-target press events.

The order is not randomized, N=1 per arm, and scheduling, process startup and temporal interactions are uncontrolled. The evidence does not prove every extra event is autorepeat, exclude queued input in other timings, establish safety with repeat off, or generalize to live apps. Turning off repeat is a changed environment and is not itself adopted as a product fix.

## R120: immediate bounded retry after one target signal failure

At source commit `226e230318b9c6a4666aa752b4c099c870a333fd`, the owner makes one immediate additional target retirement attempt through the same owned handle after a verified-identity pidfd signal error; both attempts are bounded and the first receipt is retained. Two consecutive signal failures remain UNKNOWN. The 26 target/session/Xvfb regression tests passed, including repeated-error and stopped-Xvfb cases.

One separately frozen public MCP Xvfb cell injected one pidfd `PermissionError`, repeat ON, 650 ms minimum stop; no retries. All 17 predeclared gates passed: the failed attempt remained in the receipt, immediate retry retired the bound target before resume, old input remained UNKNOWN/no replay, runtime release readback and fresh B effect passed, and old A presses stayed at one through the observed horizon. The stop lasted 650.80 ms. See [raw/r120](raw/r120) for conditions, runner, hashes and outcomes.

R118 and R119 had additional old-target presses when the failed target remained live through resume; they are historical, non-randomized comparisons, not a paired efficacy estimate. R120 addresses only a transient single failure. Repeated or persistent errors still leave the target alive and UNKNOWN, X11 input remains shared, and a passing synthetic cell does not prove real application, WSLc, MAP01, general reliability or performance.

## R121: two consecutive target-signal failures

R121 is a new, separately frozen public MCP cell at source `9500738f6c468a978b4c517c7852e654ef7464e2`, with two injected target-pidfd `PermissionError` failures followed by normal signals. Repeat was ON, and Xvfb stopped for 651.93 ms. All 17 predeclared gates passed: the cancel receipt retained both errors and UNKNOWN/no replay; the target was alive before resume; a later explicit close confirmed its exit; input release readback and the fresh-target effect and horizon passed. The raw runner, conditions, events and checksums are in [raw/r121](raw/r121).

The old target recorded one A press before stop and three by the end. The extra two occurred after resume while it remained alive; autorepeat versus queued input is not isolated here. This is counterevidence against preventing old-target effects when both immediate signals fail, despite the recovery gates passing. The injected failures were finite and ended before close; this is not a test of a permanently inaccessible target. The runner field `old_process_retired` is a pre-resume checkpoint in this variant, not an exit timestamp.

## R122: signal failure remains through close

A separately frozen public MCP private-Xvfb cell at source `2bcc85f926774a0870c98380e2cf9a0847416393` injected failures on every target pidfd signal through cancellation, resume, explicit close, and a one-second observation after close. All 10 predeclared observability gates passed: exactly four failed signal attempts through close, both cancellation and close remained UNKNOWN/no replay, runtime and independent keymap reads showed release, the old target remained alive through the horizon, and no fresh target was admitted. The old target recorded one A press before stop and two by the end. This is not a successful task-effect isolation result; the extra event remains unexplained.

After the measurement the harness explicitly terminated the disposable child for cleanup; `cleanup.old_exitcode = -15` is this harness cleanup, not a runtime recovery receipt. The test injection is not an actual permanent OS permission failure, and the bounded one-second horizon cannot prove later behavior. Raw and freeze are in [raw/r122](raw/r122).

## ViZDoom application ownership diagnostic

A separate no-gameplay-input diagnostic tested whether the existing ViZDoom Python API workflow can be passed directly as this PR's explicitly launched owned target. Its first container exited 139 before observation because the working directory was read-only; the [failed setup](raw/vizdoom-owner-r01) is preserved. A new [R02 diagnostic](raw/vizdoom-owner-r02) changed only the working directory to the existing `/tmp` convention, then launched disposable Xvfb and ViZDoom in the pinned b473 image. XRes 1.2 reported the visible game's XID owned by PID 12, whose parent was the Python launcher PID 1; the launcher was not the XRes owner. No gameplay input was sent, `game.close()` returned and Xvfb exited 0.

The current primitive binds only the exact process launched through its handle; a handle for the Python launcher would fail its digest check against the child-owned XID. An ancestry relationship alone does not authorize adopting or killing the child. A viable application adapter needs a verified ownership and lifecycle design for the actual game process (or a separately validated direct launch), independent game effect scoring, release and recovery verification. This diagnostic does not test task performance, GUI control, full application termination, MAP01 completion, WSLc or reliability.

## Direct ViZDoom executable ownership diagnostic

The [first direct-launch diagnostic](raw/vizdoom_direct_owned_launch_r01_20261030) found a visible game window, but failed XRes binding because its test script lacked a Python `__main__` guard. The spawned identity worker re-executed the script and reported a process-bootstrap error; the failed raw is retained. A separately frozen [R02 diagnostic](raw/vizdoom_direct_owned_launch_r02_20261030) added the guard and made one new no-gameplay-input attempt. It launched the pinned ViZDoom executable with Freedoom2/MAP01 arguments through `OwnedTargetProcess` on private Xvfb, observed one window, bound its XRes identity to the exact launched PID, and verified process exit after pidfd SIGTERM; identity worker exit was clean and Xvfb exited 0.

This opens a direct executable route, distinct from the Python API parent/child workflow. It does not establish that the game reached a playable level, that an independent task oracle is available through this route, that cancellation or input release is correct, or that WSLc/MAP01/full agent work is complete. The earlier Python-API process-ownership mismatch remains valid.

## Direct ViZDoom public MCP: initial environment response

A no-input [R03 screen diagnostic](raw/vizdoom_direct_screen_r03_20261030) captured a first-person game scene and HUD from the directly launched owned process. This establishes visible scene content, not playability or task effect.

Two initial fixed-order control/input comparisons were not successful: [R04](raw/vizdoom_public_owned_motion_r04_20261030) and [R05](raw/vizdoom_public_owned_motion_r05_20261030) each completed the no-input control but the input arm was refused before dispatch with `FlatTargetRefused`. The target point was specified in window-local coordinates while the MCP observation was in screen coordinates; the recorded binding placed the 640×480 window at screen origin (320,272). The failures and screenshots are preserved.

[R06](raw/vizdoom_public_owned_motion_r06_20261030) predeclared translation using the current observation binding, then ran one fresh no-input control followed by one W-down / 600 ms / W-up public MCP input cell, each on its own disposable private Xvfb and directly launched target. Both cells finished with exact target retirement. The input cell minted a reference, completed the guarded operation, recorded two emissions and a verified empty release, and independently read W up. Excluding the bottom 80 image pixels, the fraction of scene pixels changing by more than 10 in any channel between captures was 0.000254 in control and 0.776125 in input. The captured images visibly show a changed first-person viewpoint; they are not an independent position oracle. Input call duration was 722.6 ms, including the requested 600 ms wait, but this is not a matched latency or model-efficiency benchmark.

The pair is fixed-order and unseeded, and scene dynamics, focus, scheduling, image comparison and timing can confound it. It demonstrates a scoped visible environment response and release in one direct-executable public-caller input, not verified displacement, task success, cancellation recovery, MAP01 completion, WSLc transfer, model/token economics or general reliability.

## Direct ViZDoom public MCP cancellation diagnostic R07

One separately frozen [R07 cell](raw/vizdoom_public_owned_cancel_r07_20261030) ran directly launched ViZDoom on private Xvfb through the public owned-target MCP caller. A test owner injected a delayed B XTEST request and withheld the cancellation acknowledgement; the actual W key was observed down before the X server was paused. The server remained stopped for 651.11 ms. All eight declared gates passed: exact game ownership was bound; the launched game exited before resume; the old call remained UNKNOWN with replay denied; the runtime's close release readback was verified; and an independent keymap read showed W and B up. SIGTERM did not produce an exit within its grace, so the owned pidfd path escalated to SIGKILL and reported exit code -9.

This cell uses a fault-injecting test owner, not an unmodified application workload. It did not score in-game displacement or any task, observe an 8 s delayed-input horizon against a fresh window, or establish safety for other windows. It is one sample and does not establish general recovery, performance, MAP01 completion or WSLc transfer.

## Direct ViZDoom cancellation and fresh witness R08

In one separately frozen [R08 cell](raw/vizdoom_public_owned_fresh_horizon_r08_20261030), the old target was a directly launched ViZDoom game and the public MCP fault-injecting owner queued a delayed B request after the W press. The game was pidfd-retired before the private Xvfb resumed, and the original call remained UNKNOWN/no replay with release readback. A new, distinct synthetic X11 witness opened 7164.07 ms before the old delayed-B deadline. A fresh public MCP caller sent a C chord, and the witness recorded C once, W zero and B zero over at least 8.5 seconds; independent W/B/C keymap states were up. All 15 declared gates passed.

The fresh target is a synthetic event-recording window, not another game; the trial does not score ViZDoom movement, establish game recovery or prove absence of every queued input or effect. The old game exited by SIGKILL after bounded SIGTERM grace. The delayed request and acknowledgement withholding were injected by a test owner; this one cell cannot establish reliability, WSLc or MAP01 completion.

## Direct ViZDoom cancellation and fresh game R09

One separately frozen [R09 cell](raw/vizdoom_public_owned_fresh_game_r09_20261030) extended R07 to launch a new directly owned ViZDoom after the old target exited. The runner returned FAIL: 15 of 16 gates passed, but the preregistered requirement that both process ID and XID differ failed. The old game PID was 11 and the fresh game PID was 996, but **both used XID 4194320**. Their recorded process-generation digests differed. XID equality does not establish the same window incarnation, and the cell did not test stale-alias refusal across this reuse. The original failure is retained and is not recategorized as a pass.

Other observations in this failed cell: the fresh window appeared 7060 ms before the injected B deadline; the new public MCP W action completed with a verified empty release and a 0.769 scene-pixel change fraction; the independent B-keymap sampler collected 1249 samples with maximum gap 15.45 ms, observed B down zero times, and ended with W/B up. Sampling can miss short events and scene change is not an independent position score. The game target, injected fault, single trial and fixed timings do not establish recovery or general safety; MAP01 and WSLc completion remain unproven.

## Direct ViZDoom XID reuse and fresh-session refusal R10

[R10](raw/vizdoom_public_xid_reuse_r10_20261030) was a new separately frozen cell after R09, with XID reuse explicitly required; lack of reuse was predeclared HOLD. In this cell the old and fresh directly launched games both had XID 4194320, but PIDs 11 and 1007 and process-generation digests differed. The old session alias was attempted through the new public MCP owner and returned refused with `input_dispatched=false` before fresh mint. The fresh W action completed, its release receipt was verified, and the screenshot scene-pixel difference was 0.75745. All 19 declared gates passed, including original UNKNOWN/no replay and bounded old-game retirement.

The independent global B-keymap sampler took 1257 readings with maximum gap 20.48 ms and saw no B-down; it cannot exclude short key events between samples. The fresh scene change is not independent displacement/task scoring. This is one private-Xvfb fault-injection cell; it does not prove general XID-reuse safety, queued-input isolation, game task success, MAP01 completion, WSLc or reliability. R09 remains a failed cell under its original distinct-XID requirement.

## XRecord calibration and real-game recovery R11–R12

A separate private-Xvfb [XRecord calibration](raw/xrecord_key_event_calibration_r01_20261030) sent two B press/release pairs and observed the exact four events both at a synthetic focused target and in the independent XRecord device-event stream; all five calibration gates passed. This verifies one positive sequence, not loss-free recording in all conditions.

[R11](raw/vizdoom_public_xrecord_recovery_r11_20261030) added a global XRecord observer to the real-game fresh-recovery cell, but opened its X clients before launching the fresh game. The fresh XID differed, so the predeclared result was `HOLD_NO_XID_REUSE` despite the other 22 gates passing. Observer client allocation may have changed XID assignment; this is an inference, not a proven cause. The recorder did capture the fresh W press/release and no B press.

A separately frozen [R12](raw/vizdoom_public_xrecord_after_window_r12_20261030) started the recorder only after the fresh game window was created. The old and fresh games reused the same numerical XID, had distinct process generations, and the old alias was refused before dispatch. The observer was active across the injected old B deadline and recorded the fresh W press and release but no B press; independently sampled B keymap also stayed up, the fresh action and release completed, and the old call remained UNKNOWN/no replay. All 23 gates passed. The recorder's own arrival and processing are additional observation conditions; a positive W check and an 8.5 s horizon do not establish zero event loss, arbitrary-input isolation, independent game-position/task success, general reliability, WSLc or MAP01 completion. R11 remains HOLD.

## Post-trial concurrency review and regression

An independent review of PR head `93407347d3ab62105192dcbcfea310abe772dbe6` found that target retirement and handle close were unsynchronized, and concurrent cleanup could duplicate retirement. A deterministic test reproduced close occurring while a pidfd signal was in flight; a second reproduced duplicate target retirement. Both failed on the prior implementation. The candidate serializes pidfd signal/close and target-retirement receipts. A separate regression verifies a stalled identity query does not block close and cannot bind after close; it failed an initial overly broad lock and passes after moving the blocking query outside the lock. This is a code-level fix and is not retroactively part of earlier live-cell sources.

After the final change, 90 target/session/Xvfb/existing MCP-owner/cancellation tests passed in the pinned Docker image; 29 targeted tests also passed under Python `-O`. Separate unresolved review findings remain: one handle can be shared by multiple servers without an exclusive claim; target retirement can consume time reserved for independent release in a cancellation transaction; and shutdown may retire the control process before later target cleanup. These boundaries are not resolved by the concurrency locks. The PR remains draft and is not merge-ready on this evidence.

## Process-local exclusive target custody

A later candidate adds an atomic per-handle session claim. A second server using the same handle is rejected before a session starts. Each session receives a token required for binding, signaling and closing the handle; release clears the previous XRes binding and revokes that token. Verified normal close with no execution uncertainty and an exited or never-started control process releases the claim. An UNKNOWN close retains it. A stale old owner remains fenced after release, including before a new claim; an earlier draft incorrectly discarded the stale token, and its regression reproduced old-owner retirement of a newly rebound target before the fix. A supervisor-construction failure releases only its unstarted claim.

The current local suite passed 96 target/session/Xvfb/MCP-owner/cancellation tests; 35 targeted tests passed under Python `-O`. Tests cover concurrent claims, same-handle server conflict, normal transfer, UNKNOWN retention, stale tokens and stalled-identity/close races. This is process-local custody; it does not defend against malicious code in the same process or OS, automatically resolve uncertain sessions, solve transaction-deadline budgeting or shutdown timing, or retroactively change historical live evidence. Independent review and a new public live cell remain needed.
