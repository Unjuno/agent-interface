# Current-main typed-observation retention boundary — A01

This model-free construction test checks a narrow question raised by the
historical Astra telemetry audit: does the current V39/V12 measurement path
persist typed health/ammo rows and the matching full-observation row through
the session's raw event sink?

## Result

`PASS_TYPED_SIGNAL_RAW_RETENTION_BOUNDARY` on source commit
`133dafbd8f616b7d2f2ca8b14a3ba863b63f0933`.

The candidate extracts the actual nested `emit` function from current-main
`session_map01_v12.py`, supplies representative typed and full-observation
records, then checks `events.jsonl` and `delivered.jsonl`. Both files retain
the two rows in order, preserve nested health/ammo values, add integer
`emit_ns`, and match one another. A source-order check confirms the typed
event is emitted before image-artifact publication and the full observation.
The independent data-only audit rejects five nested/order/type mutations.

The exact production backend extracts the two signals from each captured frame
and calls `emit(typed)` before publishing the full image observation. The V39
controller's final `report.json` separately retains decision-level invalidation
objects and soft-event summaries. The raw observation rows and decision report
serve different roles; this test only exercises the raw event sink and its
source ordering.

## H/T/D/C/U

- **H:** On the pinned current-main source, the actual V12 session sink retains
  typed health/ammo evidence and its matching full observation in both raw
  event files.
- **T:** Extract only the real nested `emit` function from the frozen session
  source; write a representative typed row and full row; compare the saved
  files; check the real backend source order; run an independent raw auditor
  with nested-value, omission, order and timestamp mutations.
- **D:** PASS only if both files match with both rows in order, exact nested
  values and integer emission timestamps, the backend order is typed emit →
  artifact publish → full observation, and all independent controls reject.
- **C:** A mocked sink proves persistence behavior for supplied rows, not that
  a live run actually encounters a health/ammo change or records an invalidation.
  Static source ordering is not a game/backend integration run.
- **U:** No live threat exposure, monitor outcome, cancellation, release,
  independently useful feedback, recovery efficacy, progress, or terminal
  outcome was measured. #59's live lane remains unassigned.

## Reproduction

From the repository root, after checking the pinned source hashes in
`FREEZE.json`:

```sh
python3 research/doom/typed_observation_retention_a01_20261007/candidate.py \
  research/doom/typed_observation_retention_a01_20261007/out/a01
python3 research/doom/typed_observation_retention_a01_20261007/audit.py \
  research/doom/typed_observation_retention_a01_20261007/out/a01
```

The candidate uses only the Python standard library and writes to a new output
directory. `RESULT.json`, `events.jsonl`, and `delivered.jsonl` retain the first
packaged outcome. No game, model, GUI, X11 server, input device, Docker, GPU,
or formal #59 allocation was used.
