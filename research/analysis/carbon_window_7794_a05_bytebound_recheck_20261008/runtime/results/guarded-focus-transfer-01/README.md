# Stop guarded keyboard input after focus moves outside the target

A real Tk/X11 fixture reproduced collateral keyboard input through the shared
`NativeHandleBridge`: click target A, wait 250 ms, type `z`. The app transfers
focus to unrelated target B 40 ms after the click. Before this repair, guarded
execution reports `completed` and B receives `z`. The lease is still valid.

The guarded backend now checks actual X11 focus ancestry immediately before
each new key press, including the key following a modifier. Focus outside the
target stops the remaining program and the existing failure path releases held
input. Key releases remain allowed after focus loss. It does not automatically
refocus, replay, mint authority, add a watcher or take new screen captures.

| Exploratory case | Result | Independent key event |
| --- | --- | --- |
| Original source, disturbance | completed | B received z |
| Corrected source, disturbance | execution_failed at op 5 | no key event |
| Corrected source, stable focus control | completed | A received z |

All three report verified neutral release. The corrected disturbance case has
three pointer emissions, completed click/wait prefix, and no keyboard emission.
This preserves input safety on this case; it does **not** finish the intended
task. An explicit later review/recovery is still required from the caller.

Source base is `64ba776be9ebed5a8902cfa89331b90230b11e34`. This is a program-driven
live GUI regression, not a new personally interpreted model trial, frozen matched
experiment, DOOM threat exposure, useful-feedback latency or causal speedup.
The transfer fixture/runner were unchanged between the decisive original and
corrected runs. Their source copies and bridge before/after copies were saved
after those runs; they are not falsely labeled pre-run freezes. Stable control
adds an explicit no-transfer fixture option and is a separately labeled case.

Preparation failures remain in the archive:

- baseline: socket-path readiness times out before app/input. On this WSL boot,
  Xvfb's filesystem socket bind fails but its abstract socket accepts X11; the
  successor tests an actual X11 handshake. No shared socket is modified.
- baseline-02: runner uses nonexistent observation `source_sequence`; one
  read-only capture, no input. Successor uses the actual `sequence` field.
- baseline-03 and baseline-04: Tk content-window identity excludes the focused
  wrapper. Both fail at focus op 0 with zero emissions. The successor records
  the wrapper returned by the content window's actual X11 parent query. The
  explicit click offset is corrected from patch origin to [12,19].

No trial output is overwritten. Each run owns its Xvfb/app processes; cleanup
return values and stderr are retained. The fixture logs app key events and the
focus transfer independently of backend execution receipts.

Two new unit regressions failed on the original backend because it did not stop
either before the first press or after a modifier. After repair, all nine
deadline/focus tests pass. The complete local native checks pass: 340 protocol
and 151 harness tests. Their full stdout/stderr and runner result are archived.
This is a correctness repair; added X11 round-trip overhead is not measured here.

```sh
python3 runtime/results/guarded-focus-transfer-01/verify.py
python3 -O runtime/results/guarded-focus-transfer-01/verify.py
```

The raw-only verifier checks all archive members, observed key effects, genuine
focus-transfer exposure, execution failure position and neutral releases. This
does not close Issue #59 or establish reaction during a long held input, focus
change within the same target, model latency behavior, human tempo or token cost.
