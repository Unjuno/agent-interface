# Async visual motor integration and latest-observation delivery

`async_session.py` connects the frozen pixel tracker to the existing revision 2
executor, exact tile transport and PNG artifact sink. The `track_red` method
uses decoded screenshots for control, emits observations while running, checks
cancellation before issuing new motor input, and releases keys at method end.
The executor verifies release on cancellation/failure. Existing source revisions
remain unchanged; each new session records all inherited source hashes.

`async_session_v2.py` changes presentation: archive every event and image packet,
but emit only the first observation of each step automatically. `poll` returns
the latest completely prepared observation without replaying old observations.
Acceptance, step transitions, rejection, cancellation and terminal notifications
still appear immediately. Motor telemetry and command echoes remain in the log.
The terminal response includes the last image/sequence reference.

This is lossy **presentation selection**, not lossless observation gating. The
full local record remains available, but intermediate visual changes can be
missed by the planner. A latest observation is not a summary of everything that
happened. Critical visual events still need dedicated detection or escalation.

## Actual assistant sessions

Both sessions were operated by the assistant: inspect the initial screen,
submit a bounded tracking program, inspect an in-progress image, then cancel.
The local controller continued doing pixel-based motor work between those tool
calls. This proves concurrent local execution and interaction in this fixture;
it does not measure overlapping model inference computation or general ability.

| Measurement | Full stream (`async-assistant-01`) | Latest delivery (`async-assistant-02`) |
|---|---:|---:|
| Decoded/PNG frames independently audited | 216 | 227 |
| Local motor decisions | 213 | 224 |
| Accepted request to cancel request | 11.869 s | 12.170 s |
| Server cancel request to verified release | 35.68 ms | 49.84 ms |
| Cancellation matched, release verified, trailing step stopped | yes | yes |

The second session polled observation 103 while the method was active. At reply
construction, its capture age was 69.12 ms. The assistant then loaded that image
and sent cancellation several seconds later. That age excludes tool delivery,
image inspection and model reasoning; it is not planner reaction time.
Both app trajectories continued after cancellation. Their oracle files include
uncontrolled time and are retained without asserting a tracking-success score.

The first stream flooded the next tool result with old observations. Replaying
both presentation policies over the **same second-session trace** yields:

- Full event JSON: 464 records, 166,673 UTF-8 bytes.
- Compact delivery: 12 records, 3,304 UTF-8 bytes (98.02% fewer bytes).

This is a serialization replay, excluding PTY wrapping/echo, not measured model
input tokens or a controlled latency comparison. Two different live sessions
are not interchangeable experimental arms. Source and audit results are in
each session folder; `audit_async.py` checks every image against decoded packets
and rederives motor coordinates from those images. Two unit tests check missing
target failure/release and invalid tracking parameters rejecting the whole
program before input. Real target-loss/focus-change scenarios remain untested.

## Use

```sh
python3 async_session_v2.py --out ../../results-local/async-new --seed 870301 --seconds 20
```

Inspect the initial observation, then submit using its sequence:

```json
{"op":"submit","id":"track","expected_sequence":1,"steps":[{"op":"key","key":"Return"},{"op":"track_red","duration_ms":20000},{"op":"decide"}]}
{"op":"poll"}
{"op":"cancel","id":"track"}
{"op":"finish"}
```

The arena starts on Return and runs for its configured real-time duration.
`finish` closes active execution and waits for public app completion before
opening the separate scoring record. Use pipes for machine consumers.

```sh
python3 -m unittest test_async -v
python3 audit_async.py results/async-assistant-01
python3 audit_async.py results/async-assistant-02
```

Nominal tracking duration is at most 30 seconds total, in addition to inherited
step budgets. Blocking X11, PNG/file I/O or stdout can overrun timing and delay
release. There is no hard watchdog, focus guard, generic object detector or
real-time scheduler. Latest-sequence validation does not detect external screen
changes while idle. The target uses known colors in a controlled private Xvfb
fixture. Human-speed, actual token efficiency and DOOM remain unproven.

Next work should test loss/change of the target and semantically important
events against latest-only delivery, then transfer the interface to a more
realistic dynamic environment. Avoid tuning the sine-wave arena as a substitute
for the original objective.
