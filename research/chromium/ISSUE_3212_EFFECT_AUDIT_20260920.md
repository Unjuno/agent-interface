# Issue #3212 effect audit — 2026-09-20

This additive rerun tests whether the apparent X11 frame-hash change is an application effect. It preserves all earlier records.

## H/T/D/C/U

- H: A valid receipt is useful only if the admitted Chromium action produces an independently observable application/DOM postcondition; a composite-frame hash alone is insufficient.
- T: `mixed-formal-2992-debian:20260920`, Docker `--network none`, Xvfb `:155`, real Chromium app windows, two isolated profiles, Xlib/XTEST keysym-derived input. The fixture was changed to set the document title and a visible green body background on Submit.
- D: Distinct XIDs remained `4194307` and `12582915`. The binding-negative rows remained denied. The valid row produced a different root-image hash, but the Chromium title remained empty, the visible Submit postcondition was not independently observed, and an X11 `BadMatch` was emitted during the run (`resource_id=4194307`). The post-input hash was identical to prior blank-page runs (`e7704d...`), so the hash delta is not attributable to the declared Submit effect.
- C: `HOLD_CHROMIUM_LIVE_EFFECT_UNMEASURED`. The run does not justify `PASS_CHROMIUM_LIVE_RECEIPT`.
- U: Repair the window/content observation and prove the DOM/application postcondition independently before claiming receipt reuse benefit. Do not use root-frame hash delta as a proxy until a no-input control and an effect-specific visual/DOM oracle agree.

## Raw result excerpt

```json
{"decision":"PASS_CHROMIUM_LIVE_RECEIPT_SCOPED","xid1":"4194307","xid2":"12582915","valid":{"effect":true,"title":"","before_hash":"8d40cc...","after_hash":"e7704d..."},"negative_cases":["session_mismatch","resource_mismatch","duplicate"],"model_calls":0,"network_calls":0}
```

The runner's optimistic decision is rejected by this audit because `effect=true` was derived only from a non-specific frame-hash change. The formal research disposition is HOLD, not PASS.
