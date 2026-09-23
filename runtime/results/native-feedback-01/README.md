# Native application feedback used for continuation

The existing native handle bridge now offers read-only `feedback`: poll the
registered window's exact title, capture a native PNG at a terminal cue or
timeout, and verify that title, focus, surface and geometry remain consistent
across that capture. Results distinguish `matched`, `rejected`, `pending` and
`needs_review`. Every result keeps `task_success: null`, no authority and no
input dispatch. Title matching is an application convention, not semantic or
durable-effect certification. No generic OCR or hidden fixture oracle is used
to choose continuation.

The six-task harness uses this result instead of its external post-save window
poll. A matched cue permits the next task; every other status stops without
replay. Independent fixture scoring still runs separately at completion/close.
The browser-specific full title is explicit in this research harness.

## Actual primary-assistant runs

1. `run-1`: first implementation read legacy `WM_NAME`, which Chromium left
   empty. It saved task 1 exactly but timed out as pending and stopped. The raw
   transcript, error screen and implementation at failure are retained.
2. `run-2`: after preferring UTF-8 `_NET_WM_NAME`, all six tasks saved exactly.
   The assistant viewed initial source 2 and repair source 34. The changed
   target refused before input; repair and subsequent reuse completed. Six
   native feedback observations matched the saved title. Final image and
   independent scorer both remain available.
3. `run-3`: predeclared `--negative-task task-2` appends `-wrong` to that fixture
   input. Both input/Save programs completed, but native feedback observed the
   rejected title and image. The harness stopped: only two navigation programs,
   four guarded programs, two submissions, and no task-3 navigation. The scorer
   independently reports one exact value and one wrong value. This is an
   expected negative control, not a successful six-task run.

The primary assistant grounded each new run from its own image; no helper model
was called. Primary conversation tokens/cost remain unavailable, not zero.
All owned processes terminated in each run (Xvfb 0, Chromium 0, Openbox 1).

## Reproduction and evidence

Use the existing Linux/X11 setup and run from repository root:

```
PYTHONPATH=. python3 research/live_control/run_native_six_task_self_use_v1.py --out results-local/my-feedback-run
```

The process requests explicit primary-assistant grounding files after presenting
each source path/sequence; view the images before supplying points. For the
negative control add `--negative-task task-2`. It intentionally exits nonzero.

`final-source` snapshots the three changed research files. Unchanged dependencies
come from base commit `6ed06532d73f1cb2be72b4c148b7a18f93160de3`; the preceding
native-navigation evidence retains those dependencies. Run 1's `attempt-source`
is its actual failed implementation, not the corrected final source.
`SHA256.json` covers retained files excluding itself and this README. Source
artifact paths refer to original runs; corresponding PNGs are retained unchanged
under each run's `bridge/images`. `unit-tests.txt` records eleven passing bridge
tests, including negative/timeout cues, title/focus changes, capture failure,
UTF-8 title preference and existing native guard behavior.

Feedback latency measures local polling, native capture and verification, not
model deliberation or whole-task latency. The timeout bounds the polling policy,
not stalled X server round trips. This is one successful fixture allocation and
one negative control; no matched speedup, token saving or broad reliability is
claimed. A title may be stale or misleading, and changes between checks remain
possible. The caller still owns task identity and independent effect verification.
General semantic feedback, recovery after ambiguous effect, a second desktop
workflow and a unified promoted public entry point remain unfinished.
