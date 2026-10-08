# Caller-placed visual lanes through the existing native exchange

2026-09-20. A primary-assistant integration experiment for #2865/#2866, not closure
of those proposals. The assistant sees the exact native image, places rectangular
screen-pixel regions, submits an ordinary guarded action, receives the lane states
and image through the existing exchange, and decides the next action itself.

## Integration

An optional `watch_regions` list in a native harness decision declares 1..8 lanes:
each has a unique `id`, `box: [left, top, right, bottom]` in the presented full-screen
image, and `min_changed_pixels`. Registration validates and copies the exact source
pixels before any input. Invalid placement fails before the action. No default
operation path or input-authority rule changes.

After successful action completion and verified release, the watch samples the
same NativeHandleBridge capture path synchronously. All lanes use each shared
image. It ends when any threshold is met, the polling deadline is reached, or
the binding/focus/capture becomes unavailable. `watch_timeout_ms` is 0..10000,
default 1000; the interval is up to 50 ms. The deadline bounds polling, **not** a
blocking backend call; an in-flight capture can overrun it. Each sample keeps its
exact image reference. First observed states and subsequent boolean transitions
are retained alongside the latest state. Unavailable means unknown, not false.

This is one-shot sampling after a program, not monitoring during that program.
`registered_ns` marks configuration; `started_ns` marks entry to sampling, and
the first capture is the first actual observation. Transient changes before that
capture can be missed. Each stage's parent receipt identifies its operation;
lanes do not persist across stages, pause/resume, or follow moving UI elements.
No asynchronous worker, helper model, automatic next action, or task-success
inference is added. Changed pixels can come from irrelevant visual effects.

## Primary-assistant use and retained stop

Run-1, Inkscape seed 991096: the assistant placed a lane around the red rectangle
and selection-handle area, and a second lane on blank paper. After clicking, the
first sample reported zero changed pixels in both. The second reported 892 in
the object lane and zero in blank paper. The assistant saw selection handles,
then chose 15 Right chords and Save. The second watch reported 3849 changed
pixels around the object and zero in blank paper. Saved SVG parsing independently
confirms x=80, y=50, width=40, height=30; the source had x=50. Both programs report
verified neutral release. Finish was explicit at stage 3.

Run-2, seed 991097, was intended as a live unchanged-region control. Its first
click instead returned `release_unverified`, reporting the left button down.
The harness stopped before executing the watch, with recovery required and no
automatic retry. This is **STOP before watch**, not a passing timeout control.
The raw request, reply, error, releases and cleanup remain retained. Both runs'
private processes have terminal cleanup return codes; that is not proof of clean
application shutdown. The cause of the run-2 release observation is unresolved.

## Verification and limits

36 focused tests passed: 5 watch tests plus the 31 native bridge/exchange tests.
They cover two shared-image lanes, threshold distinction, one-shot consumption,
timeout/false versus unavailable/unknown, invalid configuration before capture,
and retained false-to-true transitions. Timeout and unavailability controls are
unit evidence; the attempted live timeout control did not reach the watch.

`audit.py` recomputes every retained lane count directly from PNG pairs, checks
event transitions and image identities, correlates requests/replies/sources,
independently parses the saved SVG, and checks the stopped run was not replayed.
`SUMMARY.json` contains measured local intervals; these include capture/polling
overhead and exclude primary-model reasoning and host transport. No matched
baseline, speedup, token reduction, or general reliability claim is made.

Full-screen captures and full sample receipts remain retained; this first slice
does not reduce observation payload. Program/log/event sensors, persistent lane
lifecycle, loss/duplicate handling, and compressed decision bundles remain open.
Docker was not used or restarted. Source bytes, requests, client receipts (base64
omitted), PNGs, outcomes and the release failure are archived together.

Reproduce setup with a fresh directory, then ground new requests from its images:

```sh
PYTHONPATH=.:research/live_control python3 research/live_control/run_native_calc_self_use_v1.py \
  --app inkscape --max-stages 4 --seed 991096 --out results-local/FRESH-DIRECTORY
```

Do not replay archived requests into another session. Read-only archive check:

```sh
python3 runtime/results/native-visual-watch-01/audit.py
```
