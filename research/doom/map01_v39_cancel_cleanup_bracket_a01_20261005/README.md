# V39 cancellation cleanup per-key bracket construction

This offline construction asks whether the InputOwner cancellation monitor can
retain useful per-key release evidence when it releases several held keys as a
single emergency batch. It uses the repository's fake X display only. It does
not invoke OS input, game, model, GUI capture, Docker, or a live allocation.

## H/T/D/C/U

- **H:** A verified owner-thread cancellation cleanup can retain a conservative
  keymap sample bracket and the existing actuation identity for each key in its
  batch release, even when the caller's later per-key `up` call returns
  `NOOP_ALREADY_UP`.
- **T:** Admit two distinct fake keys, request cancellation, retain the first
  owner cleanup record, and independently reconstruct key lineage and each
  pre/post sample bracket. One candidate per frozen run ID; no retries.
- **D:** PASS only if cleanup is verified neutral, both keys have confirmed
  physical-up classifications with matching down actuation IDs, sample bracket
  timestamps are ordered, the raw hash matches exact bytes, and authority and
  application-effect fields remain false.
- **C:** The bracket bounds the transition using fake display keymap samples
  around a batch release. It does not establish an exact edge time or prove
  delivery to an application. The production consumer/event serialization
  path still needs to carry this cleanup subrecord to retained run evidence.
- **U:** No live X server, physical keyboard, game, model, useful task feedback,
  threat response, bounded recovery, survival, or MAP01 progress was measured.

## Retained outcomes

- **A01:** The candidate observed verified two-key cleanup and produced both
  key brackets, but the independent audit failed because the candidate hashed
  LF bytes and Windows text output wrote CRLF. Preserve A01 unchanged as a
  candidate/auditor integration failure.
- **A02:** After fixing candidate output to write and hash the exact same byte
  sequence, one separately frozen two-key cancellation run passed. The raw
  auditor independently confirmed both matched IDs and ordered brackets. Its
  freeze covered the owner, runner, and auditor, but not every imported harness
  dependency.
- **A03:** A separately frozen run included the fake-display harness, V12 owner,
  shared executor dependency, bridge source, candidate, auditor, owner patch,
  and Python version. One two-key cancellation run passed; the independent raw
  audit confirmed both matched IDs, sample brackets, and verified neutral
  state. Raw SHA-256 is
  `36b60282cfc2a7c328cdb7c62ec0d37b029808dc7cf2f6e327d0fd954fd3c99d`.
- **A04:** The exact current-main
  `RunningActionGuardV3.record_input_released` method was source-extracted and
  replayed over the retained A03 owner-release record. The receipt retained the
  complete owner-release object, including both per-key brackets and actuation
  IDs, unchanged. Independent raw audit: `PASS_RECONSTRUCTED_SCOPED`; receipt
  SHA-256 is
  `70f286304eaa28593797be6fb20893b36dcb6c1f056f2297c09179f5334f372a`.
  This verifies the release receipt's nested-data contract, not execution of the
  controller, session, or game runtime.
- **A05–A07:** Three separately frozen composition attempts stopped in the
  source-extraction harness before producing result artifacts: A05 could not
  evaluate the source's `frozenset(...)` reason constant; A06 did not bind an
  extracted method before class construction; A07 did not bind the inherited
  lease class in the extracted method's globals. These are retained as harness
  failures and are not evidence about the product event path. No A03 evidence
  was rerun or changed.
- **A08:** A separately frozen offline composition applied the exact current
  lease interruption, executor release publisher, controller cancellation
  handoff, and guard receipt methods to the retained A03 owner-release record.
  Because zero-argument `super()` relies on Python's class-creation cell, the
  extraction harness rewrites those calls to explicit `super(Class, self)`
  references to the same parent classes. The independent audit confirmed that
  the publisher event, controller selection, and guard's pending release
  receipt preserve the complete owner-release record and both per-key brackets
  unchanged. Input authority remained false. A source-extracted terminal
  receipt then cleared the pending lifecycle flag. Result:
  `PASS_RECONSTRUCTED_SCOPED`; raw input SHA-256 is
  `36b60282cfc2a7c328cdb7c62ec0d37b029808dc7cf2f6e327d0fd954fd3c99d`;
  publisher event SHA-256 is
  `4028ca3a1dc908dc6375f840e2acd6d05f294ca67b1dc7696b4359fd085f59d7`;
  release receipt SHA-256 is
  `c97a8bc1ec56bd9900026601c993420392b0d54c31e8e348a0645e9c48b5f69b`.
  This remains source composition, not execution through the actual executor,
  process protocol, session, controller runtime, or game.

The current `session_map01_v12.py` transport statically serializes event
dictionaries with `json.dumps`, appends the same line to `events.jsonl` and
`delivered.jsonl`, and prints it; the V39 controller's stdout reader parses
each line with `json.loads`. This is a direct JSON round-trip transport, but
A08 does not execute that writer/reader boundary. No live session or game was
started for this check.

- **A09:** Source-extracted the exact V12 `emit` method and V39 controller
  `reader` and `wait` functions, then passed the retained A08 release event
  through their in-memory file/stdout/queue path. The controller wait received
  `input_released`; independent audit confirmed the decoded event and nested
  owner cleanup (including two per-key brackets) were unchanged, and authority
  remained false. Result: `PASS_RECONSTRUCTED_SCOPED`. The Windows text-mode
  log files contain CRLF while captured stdout contains LF; parsed JSON objects
  are equal. This exercises the source-extracted transport functions, not
  `session_map01_v12.main()`, a real subprocess, OS input, or the game.

The A03 source freeze includes hashes for its full imported fake-display/control
dependency closure. The A04 freeze includes the exact guard method source and
A03 raw input. The A08 freeze includes the current producer/consumer source
methods and retained A03 input. The A09 freeze includes the current session
writer, controller reader/wait, and A08 event. Reproduce only the read-only
audits with:

```powershell
python research/doom/map01_v39_cancel_cleanup_bracket_a01_20261005/audit_a03.py
python research/doom/map01_v39_cancel_cleanup_bracket_a01_20261005/audit_a04.py
python research/doom/map01_v39_cancel_cleanup_bracket_a01_20261005/audit_a08.py
python research/doom/map01_v39_cancel_cleanup_bracket_a01_20261005/audit_a09.py
```

All candidate outputs are consumed. Do not rerun them or overwrite any retained
result directory.

## A10 independent bracket audit correction

Review found that the original A03 auditor checked that each reported interval
matched the two sample finish timestamps, but did not verify sample
availability/state, each sample's own start/finish order, or that the owner
release request and XSync return fell within the sample bracket. A10 leaves all
A03 files unchanged and adds an independently frozen raw-only audit over the
same two-key fake-display cancellation trace.

The A10 auditor verifies down samples observe false→true and release samples
true→false, all samples are available and error-free, every sample interval is
ordered, and each press/release request plus XSync return is ordered inside its
pre/post sample interval. Four tests mutate sampled state, availability, sample
ordering, release bracket timing, and down request timing; all are rejected.
The audit returns `PASS_AUDITED_BRACKET_EVIDENCE`. This confirms internal
consistency of the retained fake-display measurements only; it does not prove
an exact physical edge, OS-level release, application consumption, or game
effect.

Reproduce the audit and mutation controls from this directory with
`python audit_a10.py`, `python -m unittest -v test_a10.py`, and
`python -O -m unittest -v test_a10.py`. The A03 fake-display candidate was not
rerun.
