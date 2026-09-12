# First DOOM-engine transfer: visual input through X11

The assistant has now operated a ViZDoom basic scenario through OS keyboard
input and X11 screenshots, using the existing async executor and exact image
transport. This uses the bundled **Freedoom assets**, not original commercial
DOOM assets. It is a one-room integration test, not full-game competence or a
Product Hunt-ready demonstration.

## Shared runtime transfer

[Shared runtime report](SHARED_RUNTIME.md): revision 6 now uses the pinned common
input owner/focus/lease backend. Three scripted readiness cases pass, including
cancel and expiry during a hold, with ten exact image frames. Two failed
development cohorts are retained. This adds no game-success or speed claim.

## Actual operation and retained failures

| Run | Revision | Evidence |
|---|---|---|
| `development-01` | `session.py` | Window discovery timed out before task input. Expected mixed-case title did not match the observed uppercase title in the next run. |
| `development-02` | `session_v2.py` | Actual title selection and WM readiness added. Assistant's Right-key hold visibly changed the view. Clock/score getter stayed at cached values; those measurements are invalid. |
| `development-03` | `session_v3.py` | Spectator telemetry refreshed before/after the clock probe and after control. Assistant inspected images, rotated toward the monster, discovered Space did not fire, then fired with default Control. Finish screen appeared; post-control API reported episode finished and player alive. |
| `development-04` | `session_v4.py` | Explicit `Doom.Bindings` ini replaced ineffective command-line binding setup. Assistant inspected the initial screen, fired with Space and reached the finish screen; post-control API again reported finished/alive. |

Revision 4 records the legacy successful gameplay; use revision 7 for new common-runtime trials. Old ready-event binding claims and revision 2
clock/score values are retained as failed assumptions, not authoritative controls.
The generated ini is archived after engine shutdown in the revision 4 result.

## Real-time clock and observation boundary

Mode is `ASYNC_SPECTATOR`, configured at 35 tics/second, rendering a visible
640x480 window inside private Xvfb/Openbox. Controls use XTEST keys only. No
`make_action` or API action-vector control is used. The controller sees only
screenshots/public X11 metadata; enemy position, labels and depth buffers are
not read. Setup and independent engine diagnostics use the ViZDoom API.

`get_episode_time()` alone returned an unchanged cached value. Revisions 3/4
call `advance_action(1, True)` outside each end of a two-second idle interval to
refresh spectator telemetry. There are **no advance calls during that wait**.
Both observed 71 tics over approximately 2.028 seconds, consistent with the
configured rate. These refresh calls are explicit in the source and clock log;
do not describe the entire harness as API-free or equate game tics with display
frame rate or planner decision rate.

Post-control raw reward was 98 in both finished trials. It is not used as a
wall-time-normalized performance score: spectator update cadence affects the
observed bookkeeping, and the final episode-tic getter returned zero after
completion. The completion claim rests on the inspected finish screen plus
finished/alive state after refresh, not on reward or zero elapsed time.

Key release is checked by the inherited X11 backend after each submitted
program. Local input/image timestamps and all exact packets/PNGs are retained.
The assistant still takes seconds between commands. There is no human baseline,
token-metered comparison, continuous learned motor policy or general DOOM agent.
These small development trials are not a frozen gameplay efficacy cohort.

## Reproduce

The tested environment is Ubuntu/WSL, Python 3.12, Xvfb/Openbox, system Python
Xlib/Pillow/NumPy and a separate virtual environment with ViZDoom 1.3.0.

```sh
python3 -m venv --system-site-packages /path/to/doom-venv
/path/to/doom-venv/bin/pip install -r requirements.txt
/path/to/doom-venv/bin/python session_v4.py --out ../../results-local/doom-new --seed 890401
```

Use a new output path. After inspecting the initial image, send a bounded
program using its current observation sequence, for example:

```json
{"op":"submit","id":"look","expected_sequence":1,"steps":[{"op":"hold","keys":["Right"],"duration_ms":150},{"op":"decide"}]}
{"op":"poll"}
{"op":"finish"}
```

Revision 4 binds arrows to turning/forward/back and Space/Control to attack.
Space was verified in the recorded revision 4 run; other bindings require
broader fresh validation. Choose subsequent sequence IDs from actual responses.
`finish` stops execution before reading independent engine outcome and closes
the private session. No game binaries or WAD files are added to this repository;
installed assets/configuration are recorded by hash in `environment.json`.

```sh
python3 audit.py results/development-02
python3 audit.py results/development-03
python3 audit.py results/development-04
```

Next: fresh multi-seed gameplay attempts, accurate time-to-completion and action
boundary accounting, then a longer dynamic scenario and a faithful live video.
Do not publish this basic-room success as the final demonstration.

## Primary references consulted

- [ViZDoom Python installation](https://vizdoom.farama.org/introduction/python_quickstart/)
- [Modes and asynchronous clock semantics](https://vizdoom.farama.org/api/cpp/enums/)
- [FAQ: Freedoom assets and spectator key bindings](https://vizdoom.farama.org/faq/index.html)

These sources describe the platform; the local records establish what actually
worked in this environment.

## Actual shared self-use update

[Shared self-use report](SHARED_SELF_USE.md) records an unsuccessful assistant
episode: black output after the first planner gap, retained despite frame/cleanup
audits passing. A fresh 0/20-second scripted pair did not reproduce black output,
but showed no world-crop change after its short turn. Game response and rendering
freshness are unresolved; readiness does not prove useful feedback.

## Response diagnostic update

[Four response probes](RESPONSE_DIAGNOSTIC.md) establish successful OS-key shooting
through the shared backend in one scripted trial, while Right-key rotation stays
unresolved. Extra engine refresh and delta-button availability did not fix it.
The 43 frames and release/close records audit; no candidate is promoted.

## Corrected bindings and successful shared self-use

[Binding correction](BINDINGS_FIX.md) fixes the four arrow-key names. Fresh
left/right/forward/back cases pass, and the assistant completed a basic-room
task by visually aiming and firing with normal revision 7. Nine self-use frames
and cleanup audit. Planner/tool gaps still take about 20 seconds; human-tempo
performance and the earlier black-screen root cause remain unresolved.

## Clock round-trip experiment

[Observation-anchored deadlines](OBSERVATION_DEADLINE.md) completed another actual
assistant task with zero clock commands and eleven exact frames. The second
operation interval still took 22.347 seconds; no causal speed gain is claimed.
This is a client usage pattern on unchanged v7, not architecture promotion.
