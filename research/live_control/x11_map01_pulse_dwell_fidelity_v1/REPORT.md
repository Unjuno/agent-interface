# X11 six-pulse application dwell fidelity — retained result

Task `X11-MAP01-PULSE-DWELL-FIDELITY-20260917-001`, Issue #651. Publication BASE `5d85577dd3556725bfddf6a88e379e783a13ead0`.

## Decision

**`PASS_X11_SIX_PULSE_DWELL_FIDELITY_SCOPED`**.

Twelve fresh private Xvfb/Tk sessions executed the exact temporal shape used by the #645 MAP01 deopt control: six XTEST `Right` holds, nominal 190 ms each, with 10 ms nominal inter-pulse settling. There were no formal reruns or replacement IDs.

- 12/12 sessions: exactly 12 Tk events in strict press/release alternation.
- 72/72 pulse pairs: X-event dwell within the frozen [180,230] ms integrity envelope.
- X-event dwell range: **190..192 ms**; median **191 ms**.
- Controller synchronized dwell total per case: **1140.818..1141.022 ms**; median **1140.926 ms**.
- X-event dwell total per case: **1140..1146 ms**; median **1145 ms**.
- Absolute X-event dwell minus controller dwell: median **0.833 ms**, maximum **1.870 ms** (frozen gate <=5 ms).
- extra/missing/repeat Right events: **0**.
- final Right key down: **0/12**.
- focus XID readback exact before input: **12/12**.

Frozen independent audit: 12 cases, 72 pulses, errors 0. Postformal read-only verifier: `PASS_POSTFORMAL_VERIFY`, 12/12 cases and 72/72 pulses.

## Construction boundary

Before formal measurement, setup-only construction exposed an event-loop handshake race and inherited-Xauthority failure. After those were fixed, one excluded six-pulse case produced the expected 12 events. An explored one×1140 ms hold produced 26 Tk events because X11 autorepeat began during the long hold. That long-hold shape is therefore not treated as an equivalent formal comparator.

## Interpretation

PR #645 observed a large normal-MAP01 yaw spread under admitted six×190 ms Right programs despite tightly clustered owner-side requested dwell. This experiment does **not** explain that game effect, but it removes one simple generic mechanism in this controlled X11 fixture: ordinary application-visible X event dwell did not show comparable variability. The next useful discriminator, if unowned, is game-tic/input-consumption timing rather than another owner-duration measurement.

## Audit limitation retained, not repaired

The frozen auditor correctly returns non-PASS for copied-evidence structural corruptions, but its failure-label branch can misclassify structural corruption as `X11_DWELL_DISTORTION_OBSERVED_SCOPED`. This bug does not affect the formal first outcome because the formal audit has `errors=[]`. A separate postformal verifier rejects extra-event, stuck-key, dwell-delta, and source-hash mutations 4/4 with `FAIL_POSTFORMAL_VERIFY`. The frozen auditor is preserved unchanged.

## Limits

One Linux/Xvfb/Tk/python-xlib/XTEST stack, one key, one pulse shape, no ViZDoom/game effect and no host scheduling control. X event timestamps and Tk callbacks are not evidence of the exact 35 Hz game tic at which ViZDoom samples input. No fixed-angle, cross-backend, reliability, latency, or product claim follows.
