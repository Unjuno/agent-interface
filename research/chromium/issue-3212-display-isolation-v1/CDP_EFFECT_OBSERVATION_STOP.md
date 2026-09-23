# #3266 CDP effect observation — retained STOP

Decision: STOP_CDP_EFFECT_UNOBSERVED

## H/T/D/C/U

- H: After composite identity admission, the current p2 CDP document target can receive a bounded application mutation, while the terminated p1 target is rejected.
- T: Fresh p1/p2 Xvfb and Chromium generations with explicit remote-allow-origins, fresh profiles and CDP ports; retrieve page websocket targets; close p1; evaluate the old p1 target and then set p2 document.title.
- D: Retain old-target connection outcome and p2 evaluation outcome. No OS input is sent.
- C: PASS requires old target rejection and an independently observed exact p2 effect value.
- U: No keyboard/mouse input, no X11 application effect, no production integration, no formal GUI reliability claim.

## Obstac result

- old p1 target: rejected (`OLD_TARGET_REJECTED True`)
- p2 evaluation: no expected value (`P2_EFFECT_RESULT None`)
- result: `OBSTAC_P2_EFFECT_AFTER_IDENTITY_GATE STOP`

The construction was corrected to allow the WebSocket origin, so this is not the earlier origin-permission setup stop. The p2 CDP response still did not provide the preregistered exact effect value; therefore no effect PASS is claimed.

## Next gate

Diagnose and freeze the CDP target/evaluation response schema before another formal effect attempt. Retain the composite identity predicate unchanged and require an explicit CDP success response plus an independent visible/application receipt. Do not reuse this failed allocation.
