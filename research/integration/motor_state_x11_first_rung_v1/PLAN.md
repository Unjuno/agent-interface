# Issue #27 — MotorState X11 first rung

Allocation: `motor-state-x11-first-rung-27-20260923-01`.

## H
A command/receipt-only motor state can falsely confirm current motor state after an external pointer displacement or focus transfer. A current OS/X-server readback distinguishes those directed mismatches, and missing readback must remain UNKNOWN rather than confirmed.

## T
Provided Linux execution container; Inkscape 1.4, LibreOffice Calc, private Xvfb and Python-Xlib/XTEST. Six conditions per repetition: Inkscape stable / pointer displaced / observer unavailable, Calc stable / focus transferred / observer unavailable. Three repetitions = 18 fresh app/X-server lifetimes. Each case emits one held-button or held-key gesture and verifies server-observed held state plus neutral release. External perturbation occurs only after release. Candidate classification is MATCH/MISMATCH/UNKNOWN from a separate observer connection. A scorer connection independently reads final pointer/focus and neutral input state. No model/provider, network experiment, user desktop, shared runtime, task-success claim or planner-benefit claim.

Excluded construction is retained separately and is not pooled. Formal commands are six immutable 3-case batches (one app x one repetition), each invoked once; no retry/replacement/tuning.

## D
`PASS_MOTOR_STATE_DISTINCTION_SCOPED` requires 18/18 complete cases, candidate counts MATCH=6/MISMATCH=6/UNKNOWN=6, six directed command-only false confirmations on pointer/focus perturbation, six unsupported confirmations in observer-unavailable controls, held state observed in every case, neutral release in every case, stable controls remain exact, independent audit errors=[], and >=10 copied-evidence corruptions rejected. Any complete contradictory outcome is FAIL; missing/process/setup evidence is STOP/HOLD.

## C
X-server pointer/key/focus state is not physical HID telemetry and not application effect. The command-only comparator is deliberately weak; the experiment tests the missing distinction, not a production implementation. Application focus behavior may depend on toolkit/window lifecycle.

## U
No Inkscape object-effect or Calc cell-value correctness, planner correction count, screenshot reduction, model-visible token cost, latency benefit, cross-platform reliability, hostile external input, crash/power-loss or product promotion. Directed finite cases are not natural failure probabilities.
