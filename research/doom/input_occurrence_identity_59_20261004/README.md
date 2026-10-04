# MAP01 owner occurrence identity (Issue #59)

## H/T/D/C/U

- **H:** Owner-scoped key occurrence IDs can bind a key-down admission to exactly one explicit key-up receipt or per-key cancellation interval. A scorer progress event is observed at a sample, but its actual transition lies somewhere in the bracket from the preceding sample to that sample. Even strict interval coverage can establish only a possible intent envelope, never a unique held key or causal input.
- **T:** Add occurrence IDs to V12 admissions and release receipts; construct a session-bound reducer that validates scorer/action/release evidence and uses the full detection bracket; test fail-closed cases and compare a finite set against an independent oracle.
- **D:** PASS the scoped construction if each occurrence has one matching admission and release, owner/intent/key identity agrees, one hashed semantic action binding exists, and only strict full-bracket envelope coverage yields `SINGLE_POSSIBLE_INTENT_ENVELOPE`. Cross-session, ties, incomplete coverage, multiple intents, and unverified release remain unresolved or ambiguous.
- **C:** V12 fake Xlib and synthetic records do not prove physical key-up, scorer sampling semantics beyond the bracket, game consumption, or causation. Existing V15/V16 producers do not yet attach one common `session_id` to scorer samples/events and actuation records; the reducer intentionally rejects those runtime rows until integration exists.
- **U:** No live GUI, game, model, or allocation was used. This is a construction and finite synthetic audit, not an actual-session producer integration or a claim of runtime attribution.

## Result

The private construction adds `input_occurrence_id` and keycode to V12 `input_admission`, copies the ID into `owner_explicit_keyup`, and adds it to each request-start-to-common-XSync-return entry in `key_release_intervals_ns`. The cancellation interval remains a request/sync bound; it does not identify physical per-key release time. V13's existing `input_released.owner_release` retains those IDs.

The reducer requires one non-empty shared `session_id` across scorer samples/events, admissions, normalized releases, and semantic action bindings. Every occurrence must have exactly one matching admission and release, and every admission must map to one session-bound SHA-256 action binding. A positive scorer transition is evaluated over `[previous_sample_ns, observed_sample_ns]`. It returns `SINGLE_POSSIBLE_INTENT_ENVELOPE` only when verified timing bounds strictly cover that entire bracket without endpoint ties. This does not establish one active occurrence, a held key, or causation. Multiple possible intents are `AMBIGUOUS`; other incomplete, tied, or unverified cases are `UNRESOLVED`.

This branch is stacked on draft PR #7533 at head `88cbb17c8661f94a9b7e89aba82af2eef8da6ae7`, which supplies the current-main per-key cancellation interval. The source manifest pins the common main snapshot `5d5748a85816297905ba16bbc0b342e41af22559`. No runtime session integration or main merge is claimed.

## Validation

From repository root:

```powershell
$env:PYTHONPATH='research/doom/input_occurrence_identity_59_20261004;research/live_control'
python -m unittest discover -s research/doom/input_occurrence_identity_59_20261004 -p 'test_*.py' -v
python research/doom/input_occurrence_identity_59_20261004/audit.py
python -m unittest research.live_control.test_input_transition_owner_v4 research.live_control.test_input_owner_v12_explicit_up_cancel research.live_control.cancel_release_publication_59.test_cancel_release_publication
```

The custom tests exercise reducer session and bracket validation, strict-envelope semantics, duplicate/mismatched occurrence rejection, V12 explicit and cancellation release identity under fake Xlib, and V13 event wrapping. The independent finite oracle enumerates one- and two-key placements over admission, release, and adjacent-sample bracket bounds.
