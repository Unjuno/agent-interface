# #2442 wall-clock source-time reversal estimator transfer v1

Allocation: `wallclock-source-time-reversal-2442-20260922-01`.
Additive path: `research/observation/wallclock_source_time_reversal_2442_v1/`.
Branch: `research/wallclock-source-time-reversal-2442-20260922-v1`.
Intake main `95a9f139ea7061475c4fefed88942c7b8ada3d66`; ownership reread found no #2442 PR/branch immediately before freeze.

## H
The three-sample bounded reversal rule can be transferred from logical 100 ms samples to actual wall-clock capture without treating camera return time as source freshness if the expected full displacement is computed from matched source-sample time differences and duplicate/cross-epoch/nonmonotonic source evidence yields UNKNOWN. For the supported constant-speed/at-most-one-reversal family, this should preserve zero wrong-direction output and the #1316 age gates. Delayed capture should remain safe because source time, not camera cadence, drives expected displacement. Held rendering must yield UNKNOWN when the newest three captures do not contain three strictly newer source frames.

Acceleration and a second reversal are explicit unsupported-model stress controls. Any wrong direction there is `FAIL_WALLCLOCK_MODEL_CLASS_ESCAPE`, not hidden by the supported-family result.

## T
Provided Linux x86_64 container, CPython 3.13.5, Python-Xlib/Xvfb. Private authenticated Xvfb, TCP off; no model/provider/network experiment/host desktop/user data/input actions. Producer updates an offscreen frame on an absolute 4 ms schedule and publishes it atomically by XCopyArea. An in-band source sequence is matched to the journaled source monotonic timestamp. Camera captures at six nominal 100 ms slots; source time and camera request/return times are separately retained.

Supported formal family: reversal ages 75/100/150/200 ms × post direction ±1 × phases 0/33/66 ms = 24 fresh producer cases, plus two constant-velocity controls. Fault controls per direction: one +55 ms delayed camera sample, one 310 ms render hold, one post-reversal acceleration trajectory and one two-reversal abrupt trajectory = 8 more cases. Total 34 fresh producer cases, 204 raw captures. Construction uses only REV110/P17 and HOLD130/P11 and is excluded.

Candidate uses the same newest-three decision structure and 1 px point/2 px displacement bounds as the predecessor, but expected full displacement is `73 px/s × actual matched source-time interval`. It does not drop duplicate captures: duplicate/nonmonotonic/cross-epoch source evidence returns UNKNOWN. `LOGICAL100` runs the exact predecessor fixed-7.3px rule on the same captured centroids as a diagnostic control. No action authority or downstream input exists.

One formal orchestration, no rerun/replacement/tuning. Source/gates/auditor are hash-frozen and committed/read back on the issue branch before execution. All first outcomes are retained.

## D
`PASS_WALLCLOCK_SOURCE_TIME_ESTIMATOR_SCOPED` requires complete 34-case/204-capture/process/source accounting; all matched display localization errors <=1 px; normal supported-family capture intervals are actual wall-clock observations and source identities strictly advance; candidate wrong-direction count 0 on the supported family; candidate accuracy >=0.60 at age75, >=0.95 at100, and 1.00 at150/200 over six cases/age; constant controls never emit a direction; delayed-camera controls emit no wrong direction; both render-hold controls return UNKNOWN specifically for duplicate/nonmonotonic source evidence; acceleration/double-reversal stress emits no wrong direction; missing/cross-epoch/nonmonotonic synthetic controls UNKNOWN; independent raw-only audit plus >=10 corruption controls pass; no input authority.

If supported in-model cases emit a wrong direction: `FAIL_WALLCLOCK_ESTIMATOR_UNSAFE`. If acceleration/double-reversal emits a wrong direction while supported cases remain safe: `FAIL_WALLCLOCK_MODEL_CLASS_ESCAPE`. If safe but age accuracy misses: `HOLD_WALLCLOCK_ESTIMATOR_INSUFFICIENT`. Missing/source/process/audit ambiguity is STOP/HOLD. Even scoped PASS leaves #2442 at `HOLD_DOWNSTREAM_EFFECT_UNMEASURED` because no guarded application action/effect is measured.

## C
Source timestamps are cooperative and in the same monotonic clock domain; this is not ordinary screenshot provenance. Xvfb software rendering and a saturated rectangle are easy observations. The candidate knows speed magnitude 73 px/s and the one-reversal model for its supported family. Actual application motion may accelerate, stop, occlude or violate lineage. Camera timing and source timing are distinct; neither proves task semantic currentness.

## U
No model-facing decision, task effect, physical input, cross-platform backend, compositor/Wayland, natural failure frequency, token benefit, or human-tempo claim. Same-author independent auditor is not external human review. Timing distributions are descriptive for this one allocation, not calibrated population bounds.
