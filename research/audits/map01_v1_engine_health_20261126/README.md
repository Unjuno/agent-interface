# MAP01 HUD-triggered cancellation and independently recorded engine damage

In one registered trial, the controller read a health decrease on screen and cancelled a held Up key. Across a 1.367-second interval enclosing that response, the engine recorded one additional hit and three additional points of damage taken. Engine health was 100 at both endpoints. The engine readings around the triggering frame were stale, so its health at that instant and the source of the hit remain unknown. [Machine-readable summary](SUMMARY.json)

## What the screen controller observed

The trial used source `8c91dba33f8e159f9399ba482cc8a25d18c70789`, the same saved Freedoom MAP01 V1 fixture, skill 1 and seed 26011261 as the earlier HUD trial. The one permitted program held Up for at most 4.5 seconds. The controller used the existing screen and input path. The engine witness wrote to a separate file for analysis after the run. The four neutral, one-tic refreshes qualified the post-load clock before input. The witness added zero refreshes during control. There was no firing command, injected damage, provider call or model call. [Earlier V1 HUD trial](../map01_v1_hud_cancel_release_20261126/README.md)

The controller's first six frames displayed 100% health. Frame 7 displayed 97% while the key was held. A separate passive capture of the same game window recorded 19 frames. Frames 13, 14 and 15 displayed 100%, 97% and 100%. The executor matched one cancellation to the admitted program. Its X11 input owner observed Up down before release and up afterward, then verified neutral and published release before the cancelled terminal. In this trial, 97.674894 ms elapsed from the controller's frame capture to verified neutral, including 2.343551 ms from the runtime's cancellation request.

## What the engine recorded

| Refreshed engine read | Episode tic | Health | Hits taken | Damage taken |
| --- | ---: | ---: | ---: | ---: |
| Before control | 1339 | 100 | 0 | 0 |
| After the cancelled terminal | 1387 | 100 | 1 | 3 |

Each read returned the same tic before and after retrieving the three values. Their endpoints were 1,367.271578 ms apart on the monotonic clock. The second read followed the session's existing post-control refresh. The increase in cumulative counters establishes that a hit and damage occurred within that interval.

The witness also made 36 periodic reads. All 27 reads taken between input acknowledgement and the program terminal returned tic 1339. They cannot place the recorded hit on frame 7 or establish why the HUD returned to 100%. The player-view images do not establish a firing or projectile sequence that identifies the attacker. The independent progress scorer recorded no kill, death or map exit in 36 samples.

## Retirement and integrity

The runner and service exited with status zero. The game, input owner, window manager and Xvfb process identities retired. The passive screen witness joined, and the dedicated control group and display lock disappeared.

An offline audit recomputed all 8,266 file digests in the sealed private manifest. It also recomputed the RGB digests and health readings of all seven controller and 19 passive images, checked the engine samples and timestamps, and matched the key release to the accepted input. The summary includes the registration and manifest SHA-256 digests. Raw frames, engine logs and host identifiers are retained privately.
