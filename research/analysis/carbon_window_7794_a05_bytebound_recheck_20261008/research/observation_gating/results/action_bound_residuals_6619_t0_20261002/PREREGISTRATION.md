# Action-bound visual residuals — T0 preregistration

Allocation: `ACTION-BOUND-RESIDUALS-6619-T0-WSLC-20261002-01`  
Parent question: Issue [#6619](https://github.com/Unjuno/agent-interface/issues/6619), under the real-time-control objective #59.  
Base main: `df2a230251cbb4452ae916f3e8c69c14c5b985d4`  
Branch: `research/action-bound-residuals-6619-t0-wslc-20261002`

## H — hypothesis

For valid, source-bound action receipts in a finite moving-viewport fixture, an advisory action-bound pixel residual will preserve the same scheduled external-event detections as raw full-frame change detection while generating fewer false alarms on self-induced viewport motion. It must fall back to full-frame observation whenever delivery, focus or viewport identity is invalid. This is a method result only; the null that raw deltas are already adequate remains plausible.

## T — bounded method test

Use a deterministic synthetic 16×12 grayscale raster fixture with 16 predeclared pairs, two admitted action classes (`pan_right`, `no_input`), exact synthetic request/ack/release receipts, and a separate hidden event ledger. Compare four methods under a frozen one-alert-per-pair budget: raw frame delta, action-agnostic global translation registration, action-bound conservative residual, and a foreign-intent sham receipt. The candidate may read only fixture inputs and receipts; it cannot read the event ledger. The independent auditor gets raw candidate rows, inputs, and the hidden ledger.

The fixture includes clean expected pans with no event, a one-pixel flash, a moving 2×2 object, a mandatory critical cue, under/over-delivery inside a declared transform interval, late and failed delivery, an external scroll with no input receipt, parallax, nonrigid change, occlusion, focus and viewport-generation invalidation, unchanged no-input, and an out-of-envelope transform. Every scheduled event and non-event remains in the denominator. The critical-pixel hard check is the preregistered cue transition to raster value 255 at the designated pixel; ordinary scrolling through that coordinate is not itself a cue. This hard check and full-frame fallback run in parallel with residual computation.

Primary contrast is frozen to two valid clean-pan non-events and three valid-pan event cases (flash, moving object, critical cue): action-bound alarm recall must equal raw-delta recall and its false-alarm count must be lower. Outside that matched subset, report every case and fallback outcome; do not omit adverse or unknown rows. This finite fixture does not support natural prevalence or model-facing efficiency claims.

Candidate invocation: exactly one formal WSLc container after construction checks. Independent auditor: exactly one separate network-disabled WSLc container, and only if candidate exits 0 and writes its complete raw output. No formal retries. Construction and formal output paths are separate.

## D — gates

`METHOD_PASS_SCOPED` requires exact fixture/source/image identities; complete one-to-one case accounting; independent reconstruction of raw, registration, residual, receipt binding, alert and event-deadline fields; equal primary-subset recall with fewer action-bound false alarms; zero missed critical cues relative to the raw baseline; all stale/failed/late/foreign bindings typed as full-frame fallback or rejected; all unknown rows retained; and all five corruption controls rejected. Any critical event lost by the residual is `FAIL_SAFETY_CUE_LOSS`; any mismatch is `STOP_AUDIT`; an indistinguishable event is `HOLD_IDENTIFIABILITY`. No outcome proves a live detector.

## C — conditions

No model, GUI, game, screenshot, physical or synthetic input injection, GPU, external effect, or network is used. The scene, event timing, delivery state, critical region and raster generator are deterministic and authored; the action-bound translation support is stipulated by the fixture rather than learned from an application.

## U — limits

T0 says nothing about natural event rates, application-delivered input, source-clock quality, real camera motion, moving threats, task usefulness, model-token reduction, human tempo, safety, gameplay survival, or production performance. A zero residual never means “safe”; raw frames and hard cues remain available. The action-agnostic registration comparator can explain away an external scroll, demonstrating why registration alone is not an action-causality oracle.
