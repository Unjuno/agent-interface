# Pointer focus within an observed client — 2026-09-13

The focus-stop investigation captured a concrete mismatch: expected focus XID
6291464 (Inkscape child), actual focus 6291463 (the observed active Inkscape client).
This occurred in `drag-feedback-08` using the diagnostic owner and rapid gestures.
The expected child/client relationship is recorded by the earlier snapshot's
pointer binding. It demonstrates a same-client focus transition in this failure;
it does not identify every earlier stop or prove its underlying UI trigger.

Two additional spaced diagnostic runs (06/07) passed; the rapid diagnostic run
(08) retained the failure. Timing/gesture handling remains relevant, but the
interface should distinguish same-client pointer focus from keyboard targeting.

## Unpromoted candidate

`input_owner_v6.py` changes only the pointer focus policy and adds last-input-kind
tracking. `session_v12.py` initializes it directly beneath the existing drag
feedback backend. Existing desktop and OpenTTD entrypoints remain unchanged.

For pointer admission/monitoring, both the originally observed focus and current
focus must belong to the originally observed client (client itself or descendant),
and `_NET_ACTIVE_WINDOW` must still identify that client. Missing/root focus,
unrelated original/current focus, destroyed ancestry or a different active client
are rejected. Client geometry and hit-surface checks remain in force. Traversals
are bounded at 32 ancestors; matching does not imply atomic observation or protect
against a malicious X11 client changing global properties.

Keyboard admission remains an exact focus-ID check. If keys are held while
pointer input occurs, exact focus is still required and a change releases both.
The lease's original focus/surface/geometry is not rewritten. Consequently, a
later keyboard step in the same program can still require a new decision after
a permitted pointer focus transition. This is deliberate scope separation, not
automatic keyboard retargeting. Released input and expired intents cannot be
revived by an observation.

## Evidence

`pointer_focus_probe.py` has eight controlled private-X11 checks. Its two test
surfaces/children and active-client property are explicitly set by the fixture;
this validates policy boundaries, not real window-manager behavior:

- child-to-parent and child-to-sibling transitions retain pointer hold/movement;
- keyboard input does not inherit pointer focus equivalence;
- foreign focus and a foreign active client with unchanged focus release input;
- mixed keyboard/button holds retain exact-focus release, including keymap check;
- an unrelated original focus cannot be rebound into the client;
- mismatched geometry remains rejected.

Real Inkscape follow-up used the same rapid-gesture feedback probe without the
extra 600 ms test spacing:

| Cohort | Configuration | Result |
|---|---|---|
| 09 | session_v11 with owner_v6 installed by probe | all checks pass |
| 10 | same, fresh app/profile/server | all checks pass |
| 11 | session_v12 directly initializes owner_v6 | all checks pass |

Each checks six malformed checkpoint lists before input, three completed feedback
points, and independent cancellation/expiry release while output is blocked,
with no remaining path executed after resumption. These are three scripted
integration runs, not assistant replanning, task correctness or a reliability
estimate. No feedback-latency or CPU-cost improvement is claimed; extra property
and ancestry queries may add overhead and require a later matched measurement.

`audit_drag_focus.py` verifies all 11 historical/current cohort source manifests,
131 exact AIT-to-PNG reconstructions, release and process cleanup records, the
eight boundary checks, and the captured diagnostic mismatch. Results 02/03/04/08
remain partial failures. It writes a new report without changing the original
five-cohort audit. It also fixes directory enumeration in the new auditor: the
old glob matches its own generated JSON report on a second run. Frozen original
audit source/report are retained, and this is now the repeatable audit entrypoint.

## Next gates

Pointer focus equivalence is a candidate core-semantic change/churn, not promotion
or a freeze pass. Remaining work includes cross-application regression, stale
image/input-release ordering, bounded continuation/path replacement and actual
assistant use of in-flight feedback. Original-focus child destruction still
causes refusal; dynamic GUI rebuilding is not solved. The hand-made managed-window
startup issue is independent and remains open. The earlier drag displacement
errors are not fixed by this focus policy.

```sh
python3 research/live_control/audit_drag_focus.py
python3 research/live_control/pointer_focus_probe.py \
  --out research/live_control/results-local/new-pointer-focus
python3 research/live_control/drag_feedback_probe_v8.py \
  --out research/live_control/results-local/new-drag-feedback
```
