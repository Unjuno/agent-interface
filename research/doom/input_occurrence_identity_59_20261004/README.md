# MAP01 owner occurrence identity (Issue #59)

## H/T/D/C/U

- **H:** A V12 input-owner-generated key occurrence ID can bind the exact key-down admission to either its explicit key-up receipt or its cancellation-batch release interval. A scorer progress event can be associated with that occurrence only when one validated occurrence is active and the observation falls outside the key-up/XSync boundary.
- **T:** Add owner-scoped monotonically increasing occurrence IDs at accepted key-down; preserve them in explicit key-up and per-key cancellation intervals; exercise the real V12 owner and V13 release event constructor through fake Xlib. Independently enumerate finite one- and two-key temporal layouts and compare the join against a small oracle.
- **D:** PASS scoped construction if admission IDs match exactly one release row, owner/intent/keycode identities agree, V13 forwards the cancellation record intact, unique active occurrence maps to the bound action hash, and missing/duplicate/mismatched/overlapping/release-boundary cases fail closed.
- **C:** Multiple held keys can overlap; identical key names may recur after release; malformed/missing lifecycle receipts; scorer timestamp can coincide with release request/XSync; XSync is not physical key-up or app consumption.
- **U:** Fake Xlib and finite synthetic event times only. Temporal association is not causation or proof that the game consumed input. No actual-session producer update, live GUI, game, model, or allocation was exercised. This does not yet wire occurrence rows into V15's runtime report.

## Result

The private construction adds `input_occurrence_id` and keycode to V12 `input_admission`, copies the same ID into `owner_explicit_keyup`, and adds it to each request-start-to-common-XSync-return entry in `key_release_intervals_ns`. The latter remains a request/sync bound; it does not identify physical per-key release time. V13's existing `input_released.owner_release` retains the per-key IDs unchanged.

This branch is stacked on draft PR #7533 at head `88cbb17c8661f94a9b7e89aba82af2eef8da6ae7`; #7533 supplies the current-main per-key cancellation interval. This candidate adds occurrence identity to that interval and to explicit admissions/up receipts. The source manifest pins the common main snapshot `5d5748a85816297905ba16bbc0b342e41af22559`. No runtime session integration or main merge is claimed.

The scorer join accepts an event only when exactly one admission/action binding/release lifecycle is valid. It labels an event during the release request/XSync window `unresolved_release_boundary`, overlapping active keys ambiguous, and missing or nonunique evidence unresolved. A unique result explicitly sets `causation_claimed=false`.

## Validation

From repository root:

```powershell
$env:PYTHONPATH='research/doom/input_occurrence_identity_59_20261004;research/live_control'
python -m unittest discover -s research/doom/input_occurrence_identity_59_20261004 -p 'test_*.py' -v
python research/doom/input_occurrence_identity_59_20261004/audit.py
python -m unittest research.live_control.test_input_transition_owner_v4 research.live_control.test_input_owner_v12_explicit_up_cancel research.live_control.cancel_release_publication_59.test_cancel_release_publication
```

The custom tests invoke the modified V12 owner methods under fake Xlib, check explicit and cancellation release identity, and exercise Executor V13's event wrapper. The independent finite oracle checks all discrete one- and two-key placements over the enumerated acknowledgement, release-request, and sync-return states.
