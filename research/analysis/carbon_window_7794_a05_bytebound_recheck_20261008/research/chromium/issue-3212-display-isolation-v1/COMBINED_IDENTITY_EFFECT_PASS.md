# #3266 combined identity and p2 CDP effect gate v1

Decision: PASS_COMBINED_IDENTITY_EFFECT_SCOPED

## H/T/D/C/U

- H: After p1 teardown and fresh p2 display/profile/process allocation, composite identity evidence rejects the old p1 CDP target even when XID is reused, while the admitted p2 target returns one exact bounded application effect.
- T: Fresh Debian bookworm-slim; Chromium/Xvfb/Openbox/xdotool; p1 on :211/CDP 9321 and p2 on :212/CDP 9322; retain page websocket URLs, XID, WM_PID and process identity; close p1 before p2; attempt old target then current p2 mutation.
- D: Retain both negative and positive results. No OS keyboard/mouse input is used. Effect receipt must be exact and exception-free.
- C: PASS requires old target rejection, p2 value p2-admitted-effect, distinct p1/p2 websocket identities, and recorded XID reuse without trusting XID alone.
- U: No OS input, no user-facing application task, no cross-application reliability, no full #3266 formal p1/p2 action allocation, no production integration.

## Obstac result

OBSTAC_COMBINED_IDENTITY_EFFECT PASS old_target_rejected=True p2_value=p2-admitted-effect

- p1: display=:211, CDP port 9321, XID 4194307, WM_PID 6194, page websocket ws://127.0.0.1:9321/devtools/page/7A929CA72E18AE770F07FDDA70ADCDAE
- p2: display=:212, CDP port 9322, XID 4194307, WM_PID 6347, page websocket ws://127.0.0.1:9322/devtools/page/A3F0DA59223A3AB6B1C300B0CEA5BF03
- old p1 target: rejected
- p2 effect: exact value p2-admitted-effect; no exception

The XID was reused, but the old CDP target was not admitted. The current p2 target was admitted only after the composite generation checks and returned the bounded effect receipt.

## Scope and next gate

This closes only the combined identity/effect construction gate for this pinned Chromium/Xvfb fixture. It does not establish OS input safety, application-level correctness, cross-application reliability, or product readiness. The next gate must add a positive p2 OS-input/application-effect control and stale old-process/old-target negative controls without weakening the composite predicate.
