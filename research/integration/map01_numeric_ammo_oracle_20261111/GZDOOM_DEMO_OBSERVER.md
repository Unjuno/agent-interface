# MAP01 post-release game-command observer candidate

Status: bounded parser implemented and accepted actual no-input demos from
the pinned g4.14.2 binary. R117 confirmed a visible foregrounded MAP01 capture
path and R119 sampled the `vid_fps` overlay in matched record-off/on arms;
positive-forward parser qualification, tic-to-QPC mapping, recorder-overhead
measurement, and live delayed-event acceptance remain open.

## Finding

The retained R104 run used GZDoom `g4.14.2` (`gzdoom-stdout.log`, executable
SHA-256 `ec706c2ea1ef946eec13be7b1b461df8d52efcd47caa6c056ed0e0257f7f9ffa`).
The upstream `g4.14.2` source provides a promising observer path:

- [`d_main.cpp`](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/d_main.cpp)
  checks `-record`, begins demo recording for the selected map, and starts the
  game. This avoids sending a console command during the measured operation.
- [`g_game.cpp`](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/g_game.cpp)
  builds `usercmd_t` from button state. `Button_Forward` contributes to
  `forwardmove` and sets `BT_FORWARD`; while recording, the game writes the
  per-tic user command through `G_WriteDemoTiccmd`.
- [`d_protocol.cpp`](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/d_protocol.cpp)
  defines the delta-coded user-command serialization. The demo container has
  an IFF `FORM ZDEM`, a `COMP` size field, and a `BODY`; when compression is
  beneficial the body is zlib-compressed.

Thus a decoded post-release `BT_FORWARD`/positive `forwardmove` command would
be evidence that GZDoom's game tick consumed forward input. It would be
stronger than `GetAsyncKeyState`, which only observes current sampled key
state. A neutral demo command stream would still not prove that no Windows
message was queued or delivered and ignored, and a movement command is not by
itself proof that the player position changed.

## Qualification gates before live use

1. Implement a bounded, strict parser for the exact g4.14.2 IFF/ZDEM and
   `usercmd_t` format. Reject malformed sizes, unknown command layouts,
   truncated compressed bodies, absent stop markers, and wrong version/map.
2. Validate the parser against a demo emitted by the pinned executable with a
   separately scheduled, known forward-key positive control and a no-input
   negative control. Retain the binary demo files and expected command-tic
   ranges; do not synthesize the only accepted fixtures.
3. Establish a conservative link between game-tic index and the external
   monotonic/QPC timeline. The demo format records command order, not wall-clock
   timestamps. Until the mapping uncertainty is bounded tightly enough to
   distinguish lease terminal and post-release horizon, command presence is
   only a session-level signal, not a post-terminal finding.
4. Measure whether `-record` changes frame/tick cadence or recovery timings.
   Any claimed timing comparison must use the recorder in both matched arms or
   quantify its overhead separately.
5. Keep the existing independent release receipt and neutral key-state horizon.
   The demo is an additional game-consumption witness, never a replacement for
   custody/release or task-effect evidence. Use a fresh owned generation and
   preserve UNKNOWN processes unchanged.

## Current disposition

Gate 1 is implemented in `gzdoom_demo_v4142.py`. It bounds the FORM/file/body
and tic counts; checks version, map, header, single-player UINF, chunk and
compression framing; reconstructs delta button groups and signed usercmd
fields; and rejects special opcodes it cannot parse safely. The exact format
details were checked against the official [`d_protocol.cpp`](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/d_protocol.cpp)
[`d_net.cpp`](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/d_net.cpp),
[`g_game.cpp`](https://github.com/ZDoom/gzdoom/blob/g4.14.2/src/g_game.cpp), and
[`constants.zs`](https://github.com/ZDoom/gzdoom/blob/g4.14.2/wadsrc/static/zscript/constants.zs)
at tag `g4.14.2`. It preserves state for `DEM_EMPTYUSERCMD`, handles the
observed `DEM_SETPITCHLIMIT` special command, and accepts the writer's
unterminated UINF payload only when its NUL is present as the zero-valued IFF
odd-byte pad. `BT_FORWARD` is bit 13 (`0x2000`); bit 0 is `BT_ATTACK`. Demo
recording also sets `usergame=false`, so enabling it changes game state and
must be qualified as an instrumentation condition.

The retained R01 demo is the first actual-binary cross-check: 1,922 bytes,
zlib-compressed body, MAP01, one player, 2,261 decoded tics and one pitch-limit
special command; every decoded tic has `forwardmove=0` and no `BT_FORWARD` bit.
Its SHA-256 and the complete observation limitations are in the private packet
`map01_demo_observer_qualification_20261111/r01_result.json`. This is a useful
no-forward sample but not a timing-matched negative control: the planned five
seconds was not measured, and unrelated physical host input cannot be excluded.
One parser bug found by this file was the UINF pad-byte terminator; another
source review corrected the `BT_FORWARD` mask from bit 0 to bit 13.

R02's positive W control was withheld because fresh R01, no-record R03, and
software-renderer R04 all showed black client areas in computer-use capture.
Independent GDI PrintWindow and screen BitBlt reads of preserved R97 were also
black. The same pinned launch/config recipe had a visible retained R104 image,
so the current rendering/capture failure remains unexplained; Windows System
and Application event logs showed no matching GPU reset or GZDoom error from
13:30–14:30 local time. R97 PID 55376 remains preserved and received no input
or close action. The R01 and R03/R04 outcomes and hashes are retained in the
packet. MAP01 positive input, app-effect adjudication, clock alignment and
recorder-overhead gates remain open. No further game input is authorized by
this packet until the exact target screen can be observed.

## Follow-up display and cadence evidence (2026-11-11)

The prior black-window result was narrowed. R115's exact-HWND CUA screenshot
was black while the target was a background window. R116 independently showed
that the protected R97 PID 55376 remained the foreground root, and correctly
skipped a physical-screen capture under a no-activation preregistration. In
R117, a fresh exact-owned PID 40388/HWND 76680474 was explicitly activated;
CUA and the runtime's `Win32Backend.observe_read_only(screen_physical_px)` then
both showed MAP01/HUD/`vid_fps`. This supports foreground/capture-path mismatch
as the cause of the earlier black captures; it does not prove all GZDoom
rendering failures are resolved.

R114 measured one record-on no-input session interval of 5.007377 s and parsed
177 commands (35.348 commands/s); its title-polling and first-tic uncertainty
prevent precise per-tic timing. R119 ran six visible one-second-spaced
`vid_fps` samples in each no-input arm. Both record-off and record-on displayed
120 fps in all six samples; rounded frame-time labels were 8/9 ms off and 8 ms
on. This small fixed-order pair shows no difference at the overlay's integer
FPS resolution, not absence of recorder overhead. R119's record-on demo parsed
1,263 session tics with no `BT_FORWARD`/positive `forwardmove` or `BT_ATTACK`,
but the full recording has no QPC event mapping. The visible foregrounded
capture route is now established for a fresh owned process, so a separate
preregistered positive W control can proceed. Retain all exact-call recovery,
release and task-effect checks; do not use this overlay pair as a substitute
for tic-level delayed-command evidence.

**2026-11-11 R120 positive-forward control:** R120 target was visibly MAP01/HUD (ammo 50); fresh owned PID 3892/HWND 210110894 was exact foreground. W down/up call brackets spanned about 505 ms; `GetAsyncKeyState(VK_W)` observed down and no later down occurred during the 2.2 s horizon (maximum sampling gap 1.109 ms). But the actual pinned demo had 4,578 MAP01 tics and zero non-neutral commands. This fails to prove app consumption and cannot establish absence of delayed input. R120 is `FAIL_OR_UNKNOWN`; no retry within the attempt. Exact owned process closed by WM_CLOSE; exit code not captured; protected PID 55376 untouched. Fourteen raw-manifest entries verify. Next inspect pinned Windows input acquisition/demo recording paths and require a new positive control with app-level command/effect evidence before another expiry trial.


## R120 positive-control failure and next discriminator (2026-11-11)

R120 supplied the first visible, foregrounded known-W attempt with this parser,
but the positive-control gate failed: the Windows async-key sampler observed
W down for about 505 ms while the actual pinned g4.14.2 demo contained 4,578
MAP01 tics and no non-neutral command. The exact-owned PID/HWND remained
foreground in the sampler. This is not evidence that GZDoom consumed W or that
no delayed command reached it. It could reflect backend injection/focus or
GZDoom input acquisition, a control-flow/config issue, or an issue in our
parser's real-positive path; existing neutral demos do not discriminate these
causes. R120 raw data and FAIL_OR_UNKNOWN classification are retained in its
private packet.

Pinned upstream `g4.14.2` source confirms `G_BuildTiccmd` constructs a tic
command from button state, maps `Button_Forward` to positive forward movement
and `BT_FORWARD`, and the demo protocol serializes non-neutral per-tic commands
(`DEM_USERCMD`) while neutral commands can use `DEM_EMPTYUSERCMD`. The source
path describes what would be recorded if the game tick consumed the binding;
it does not prove the R120 backend injection reached that path. Microsoft
documents `GetAsyncKeyState` as reporting the key's current state when called,
not application receipt. Therefore R120 establishes a system key-state
transition only.

Next, run a new separately preregistered **positive app-consumption control**
on a fresh visible MAP01 target: send one bounded W hold and require both a
real positive/forward command in the emitted pinned-version demo and an
independent post-action movement effect, while preserving exact HWND, baseline,
input/release QPC brackets, and all raw evidence. This first tests parser +
input delivery only; it must not be combined with expiry/recovery or used as
late-event evidence. If the command is absent, stop and inspect active binding,
foreground/focus transitions, backend key injection semantics, and demo
recording order before another action. If it appears, only then design a
timed command-to-QPC alignment experiment with an independently observable
neutral interval. Do not infer delayed-event absence from a session-level
neutral demo.


## R121 scan-code positive-control result (2026-11-11)

A new fresh exact-owned process used explicit scan-code W input. It reached
visible foreground MAP01/HUD; one ~500 ms W down/up produced 17 consecutive
positive forward/`BT_FORWARD` commands in the actual pinned demo (tic 2099–2115,
3,503 tics total), with no attack. Independent pre/post screenshots show the
player advanced and 87.7421% pixel difference. The QPC-sampled system key
state showed the hold and remained up for 2.2 s after release. This validates
one positive parser/input-consumption sample for scan-code and a separate
visible movement effect. R120's default virtual-key attempt had no game command,
so scan-code is a plausible mechanism difference; nonmatched config/order means
not a causal result. Neither R121 tic numbers nor the neutral external key-state
horizon proves absence of delayed app commands. See private packet
`map01_positive_forward_scan_code_20261111_r121/`. Next, ensure the supervised
public operation preserves explicit scan-code and carry the parser into a
separate lease-expiry/recovery trial with bounded command/QPC alignment.


## R122 QPC alignment calibration

A fresh MAP01 record-on run issued three scan-code W pulses. Its pinned-parser
demo contains three 18-tic forward clusters at 1098–1115, 1134–1151, and
1171–1188. With external QPC/GetAsyncKeyState brackets around each input and
neutral transition, pinned `g4.14.2/src/doomdef.h` `TICRATE=35` supplies a
35 Hz model. Under the preregistered edge constraints (command transition
after input call start, and within one tic of paired key-state transition),
the six edge constraints share a 12.867 ms intercept interval, below the
20 ms criterion. Max sampler gap was 1.1898 ms; there were no W-down samples
after last release across 2.2 s; independent screen captures showed forward
movement. This is process-local calibration, not a delayed-event or recovery
pass. R123 must recompute an in-process fit and preserve UNKNOWN if uncertainty
exceeds 20 ms. Raw packet: `map01_positive_forward_tic_qpc_20261111_r122/`.
