# #4255 guarded wall-clock reversal effect v1

Allocation: `wallclock-reversal-effect-4255-20260923-01`.
Parent evidence: #2442 allocation-02 `HOLD_WALLCLOCK_ESTIMATOR_INSUFFICIENT`; this allocation does not rerun capture.

## H
The #2442 newest-three source-time reversal decision, when bound to a fresh session/epoch/window receipt, produces exactly one matching XTEST/application effect for recent supported LEFT/RIGHT decisions and produces no input/effect for age200, duplicate-source, cross-epoch or stale-decision evidence. Every action ends X-server key-neutral.

## T
Fresh private Xvfb + separate Xlib application process per case. Exact candidate constants: 73 px/s, 2 px displacement bound, newest-three source records, dynamic source-time interval, duplicate/nonmonotonic/cross-epoch -> UNKNOWN. Effect freshness ceiling 150 ms. Six schedules × two repetitions =12 sessions in two immutable six-case batches. CROSS_EPOCH_OR_STALE rep0 is cross-epoch; rep1 ages an otherwise-valid receipt by 170 ms. Recent decisions dispatch one XTEST arrow press/release; refusals dispatch none. Retain source request, candidate/admission, XTEST request, app event/effect, keymap, process exits.

## D
PASS only with 12/12 complete cases: RIGHT/LEFT recent produce +1/-1 exactly in 2/2 each; eight refusal sessions produce input0/effect0; action sessions have exactly one press+release and neutral final keymap; all foreign binding probes refuse; independent auditor errors=[]; 12/12 corruption controls reject; formal invocations/reruns/replacements/tuning=2/0/0/0. Wrong/cross-session/stale effect is FAIL; missing expected recent effect is HOLD/FAIL_EFFECT_DELIVERY; incomplete provenance/process/release is STOP/HOLD.

## C
Cooperative Xlib key-effect sink; key effect is not generic task success. Source triples are exact contract fixtures and provide no new capture reliability evidence.

## U
No model, natural reversal frequency, screenshot/capture estimate, token/latency gain, physical HID, Wayland/cross-platform or production claim.
