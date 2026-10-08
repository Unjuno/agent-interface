# Read-only state evidence after native release failure

The second primary-assistant visual-watch allocation stopped with
`release_unverified` and left-button-down evidence. Its owner immediately tore
down the private display, so that retained run cannot tell whether the state
persisted or changed shortly afterwards. See
[the unchanged original record](../native-visual-watch-01/README.md).

The existing native harness now records three read-only follow-up samples before
teardown when a failed action requires recovery. It queries the full X11 keymap
and core pointer-button mask at target offsets 0, 10 and 50 ms. These are separate
reads, with separate timestamps, not an atomic snapshot. A blocking Xlib query
can exceed the target offset. Query failure is retained as unavailable, never
converted into an empty/neutral state.

The diagnostic does not send releases, retry the program, clear sticky recovery,
or turn a failed action into success. Its coverage is explicit: keycodes 8..255
and core pointer buttons 1..5; extended buttons are not observable through this
mask. There is no blanket claim that all physical controls are neutral. Sampling
all keycodes also avoids relying on the backend's local held-key dictionary for
this diagnostic. The underlying release implementation is unchanged.

## Evidence

A programmatic control used one dedicated Xvfb and a separate fixture connection
to set three conditions: initially up, key `a` plus left button held, and then
released by that fixture. All nine samples matched their condition. The diagnostic
backend recorded zero emissions. The fixture itself emitted four state-setting
events and two explicit cleanup releases; zero-input applies only to diagnostics.
Private Xvfb/WM processes were terminal after cleanup (codes 0 and 1).

39 focused tests passed, including untracked physical keys, changing button state,
unavailable/malformed input queries, and continued INPUT_RECOVERY_REQUIRED after
diagnostic sampling. The earlier 39-test pass preceded the added assertion that
the actual session still refuses input; the retained tests.txt is the later run.
The existing CI boundary test step includes these new tests.

This is diagnostic capability validation, **not** reproduction or explanation of
the prior live failure. It does not prove that a release race caused that failure,
nor that waiting repairs it. The first naturally failing future native allocation
will provide the missing post-failure trace. This control does not constitute a
new model-use, task-success, latency, or token-efficiency result.

Run the control in a fresh directory:

```sh
PYTHONPATH=.:research/live_control python3 research/live_control/probe_native_release_observation_v1.py \
  --out results-local/FRESH-DIRECTORY
```

Read-only retained-evidence audit:

```sh
python3 runtime/results/native-release-observation-01/audit.py
```
