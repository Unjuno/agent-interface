# MAP01/V12 direct-window continuity transfer

Goal: carry the standard guarded caller's lifecycle evidence into the selected
V39 -> V15 wrapper -> process backend -> Executor/V4/V12 input-owner path.
Scope is local Fake X construction only; no formal/live allocation.

- [x] Reuse one dedicated lifecycle IdentityReader for capture and pre-press
  checks. Independent reader-local tokens cannot be compared across epochs.
  Borrow that reader in V12 while keeping its input connection and process/focus
  reader separate. The backend owns lifecycle-reader retirement.
- [x] Bracket capture, publish target_window_identity alongside process evidence,
  bind the complete observation/lease/deadline once, and check the retained token
  before input and periodically while held. Preserve release bypass/telemetry.
- [x] Serialize the shared reader's request slot with original-deadline/cancel
  polling; no unbounded lock wait and no second observer fallback. Initial healthy
  collision failures remain in the construction record rather than being hidden.
- [x] Add --target-window-lifecycle requiring process identity and the measurement
  session. Forward the flag, remove wrapper-only flags before base parsing, and
  retain the selected policy in source metadata.
- [ ] Run the affected isolated MAP01 entry normal/-O, retain raw first failures,
  source identity and final results, review and integrate with actual protection.

Required controls: healthy source/admission/release, same-process same-XID stale
refusal, capture-time destruction, final source mutation, held-read cancellation/
expiry and overlapping capture, plus wrapper/launcher selection and legacy modes.
No server-issued incarnation, atomic check/use, arbitrary event-loss detection,
native input/readback bound, task recovery/effect or efficiency claim follows.
Concurrent capture may consume the finite local query budget and retire the
monitor; availability/cost still need qualification. Never rerun old allocations
to turn construction success into a live result.
