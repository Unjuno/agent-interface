# Primary-assistant transfer from Chromium to Calc

This transfers the existing native handle bridge and feedback method to an
actual LibreOffice Calc task. The setup and independent saved-file evaluator
are reused from `research/observation_gating/gui_suite.py`. The assistant views
each native screenshot and supplies a guarded point and native keyboard tail.
No research Driver input, helper model, spreadsheet API editing or file oracle
is used to choose actions. Setup creates the blank workbook; saved-file scoring
runs only after the assistant explicitly finishes.

Goal: seed 991084, save A1=116 and A2=476 in the private `sheet.xlsx`.

## Attempts and recovery

* `run-1`: the selected blank portion of the name box was visually flat. The
  existing store rejected target minting before any program dispatch. Retain
  the source, request, traceback and blank output workbook.
* `run-2`: the assistant selected the visible name-box text instead. Entry and
  Save completed, then focus moved to Confirm File Format. Native feedback
  returned `needs_review` with a root image instead of confirming a task score.
  That image also showed A1=16, not the intended 116; A2 was 476.
* The assistant explicitly clicked Use Excel 2007-365 Format. The dialog was
  destroyed; feedback on that registered window retained `BadWindow` and
  returned `needs_review`. The harness presented the newly focused main window
  for a new explicit assistant decision, without automatic input.
* The assistant selected A1 from the fresh image, entered edit mode, selected
  its content and replaced it with 116 using separate character operations and
  explicit 30 ms gaps, then saved. A fresh final image showed 116 and 476.
  After explicit finish, the existing independent evaluator and an additional
  openpyxl read of the retained workbook both confirmed `[116, 476]`.

This is successful completion **with recovery**, not clean first-pass transfer.
The first input's missing repeated digit is observed but its cause is unresolved.
The repair changes edit mode, selection, pacing and application state; it does
not isolate which condition matters. The intermediate wrong value was visible
and its Save was requested; no intermediate workbook snapshot was retained, so
only the final persisted value is independently verified.

## Evidence and limits

There are three completed guarded programs with verified release in run 2.
Feedback states are `needs_review`, `needs_review`, `matched`; all retain null
task success and no feedback-granted input authority. Nineteen native PNG/hash
links were verified. The 80-file SHA256 manifest excludes itself and this README.
Raw artifact paths identify original runs; copied PNGs remain unchanged.

`source` retains the new harness and reused setup/bridge sources. Other unchanged
dependencies are pinned by base commit
`64651bc61d3f6f78626a73e605f6caad5207369a`. Both attempts used the same code.
The harness deliberately bounds interaction to four presented stages and does
not retry partial or refused native programs. Each new stage registers the
current focused window and waits for a fresh assistant decision before input.
This is explicit research orchestration, not a unified promoted public caller.

All three tracked subprocesses were terminal in both attempts: Xvfb 0,
Openbox 1, LibreOffice launcher 255 after fixture teardown. This does not claim
all processes exited successfully or prove a complete descendant-process audit.
There were no helper-model calls; primary model tokens/cost remain unavailable.
The three local action-plus-feedback durations were about 918, 662 and 1053 ms,
excluding assistant wait and image review. No matched benefit or human-tempo
claim follows from them. This is one additional task allocation in a second
application, not broad held-out evaluation.

Reproduce in the existing Linux/X11 environment:

```
PYTHONPATH=. python3 research/live_control/run_native_calc_self_use_v1.py --out results-local/my-calc-transfer
```

View each presented image, then supply its exact source sequence and point/tail
or explicit finish in the requested file. The expected title is a cue only.
Next address repeated-character delivery and explicit post-dialog observation
handoff using this retained failure, before claiming reliable native transfer.
