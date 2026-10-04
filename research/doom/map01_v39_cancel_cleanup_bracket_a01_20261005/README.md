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

The A03 source freeze includes hashes for its full imported fake-display/control
dependency closure. The A04 freeze includes the exact guard method source and
A03 raw input. Reproduce only the read-only audits with:

```powershell
python research/doom/map01_v39_cancel_cleanup_bracket_a01_20261005/audit_a03.py
python research/doom/map01_v39_cancel_cleanup_bracket_a01_20261005/audit_a04.py
```

All candidate outputs are consumed. Do not rerun them or overwrite any retained
result directory.
