# Bounded drag feedback candidate — 2026-09-13

Follow-up: [pointer focus investigation](POINTER_FOCUS.md) records a same-client
child-to-parent transition and tests a pointer-only equivalence candidate. Use
`audit_drag_focus.py` for repeatable auditing of all cohorts; the original auditor
also matches its own generated JSON file after its first run.

New unpromoted `session_v10.py` / `session_v11.py` add intermediate observations
to the shared bounded drag. Existing `interactive_v11.py` still uses session_v9;
the similarly numbered files are different entrypoint/backend version series.
No established runtime or previous experiment source was modified.

`pointer_drag.observe_at` selects 1–4 unique increasing point indices before the
final point. At those points the worker publishes a checkpoint, captures an exact
image and publishes its sequence. The independent owner retains the original
focus/surface/geometry/deadline and handles cancellation, expiry and release.
There is still no in-flight path replacement: a reader can observe or cancel;
the predetermined remaining path otherwise continues. This is a prerequisite for
live manipulation, not a completed closed-loop replanning interface.

Session_v11 additionally accepts `feedback_delay_ms` (0–250, default 0) before
each checkpoint capture. This explicit cooperative wait is included in the
10-second aggregate declared hold/wait budget. It is not an application paint
barrier. Capture/serialization add further wall time and the original lease still
bounds input validity. There is no automatic app-specific delay or compensation.

Example candidate step:

```json
{"op":"pointer_drag","points":[{"x":619,"y":390},{"x":631,"y":390},{"x":643,"y":390},{"x":655,"y":390}],"duration_ms":300,"observe_at":[0,1,2],"feedback_delay_ms":60}
```

## Actual-app evidence and failures

All five cohorts used a private Inkscape fixture with real X11 input. They are
scripted integration tests, not assistant gameplay or a performance comparison.

| Cohort | Candidate/probe | Outcome |
|---|---|---|
| 01 | session_v10 / initial probe | validation, three checkpoints, blocked-output cancel/expiry release pass; checkpoint images do not yet show object movement |
| 02 | session_v11 / probe_v2 | completed checkpoints and cancel pass; expiry setup instead hits focus-change rejection |
| 03 | session_v11 / probe_v3 | completed-drag expectation fails with needs_decision; inter-fault spacing was not reached |
| 04 | session_v11 / probe_v4 | same focus rejection despite spacing/fresh observation before the completed drag |
| 05 | session_v11 / probe_v5 | all checks pass with additional focus-diagnostic owner instrumentation |

The probe revisions preserve failures. Six invalid checkpoint lists are rejected
before an otherwise valid leading click. Completed runs publish feedback at three
points and verify final release. Fault checks deliberately block the worker's
checkpoint output callback, then observe the button from a separate X11 client.
Cancellation and expiry release it while output remains blocked; after output
resumes the remaining path does not execute. This simulates an output stall,
not a directly injected ImageGrab/X-server stall. Existing owner lifecycle tests
remain separate evidence for server failures.

Cohort 05's final intermediate image shows rectangle bounds moving from about
x=597…643 to x=608…655 before the final planned point. In cohort 01 all three
intermediate images retain the old bounds. The 60 ms delayed variant therefore
produced useful object feedback in one run, but is not a deterministic readiness
guarantee or a verified accuracy improvement. No task file was scored in this
integration study; the prior displacement study remains authoritative for that.

Focus-change releases are real observed stops. Rapid gestures/double-clicks were
considered as a possible cause, and 600 ms inter-gesture spacing plus a fresh
snapshot was tried; it did not establish a fix. `input_owner_diagnostic.py` differs
from owner_v5 only by recording expected/actual focus on mismatch. Its successful
run did not reproduce the failure and therefore does not identify the cause.
Instrumentation can change timing. Do not weaken focus guards or claim this
problem resolved based on the passing fifth cohort.

`audit_drag_feedback.py` verifies source hashes, all 58 exact AIT/PNG images,
terminal release records, successful owned-process cleanup, and retains each
partial failure in `results/drag-feedback-audit.json`.

## Remaining contract work

- An image is historical: the owner can release during capture/output. Checkpoint
  metadata says capture was requested before planned release, not that the button
  is currently held. Existing snapshot capture has no atomic held-state proof.
- Session_v10 can emit a feedback record after independent expiry; its deadline
  stays unchanged. Session_v11 checks validity before its cooperative delay, but
  expiry during capture remains possible. Consumers must not treat late feedback
  as new input authority. Explicit freshness/release ordering is still required.
- Define bounded continuation/replacement and post-action observation age, then
  test active replanning with an actual assistant, not just scripted callbacks.
- Investigate transient child/top-level focus changes with adequate diagnostics;
  retain exact keyboard focus semantics and independently test any pointer change.
- The previous hand-made-window startup failure remains a separate open issue.

This adds candidate core semantics/churn. It is not promotion, freeze qualification,
human-speed parity or token reduction.

```sh
python3 research/live_control/audit_drag_feedback.py
```
