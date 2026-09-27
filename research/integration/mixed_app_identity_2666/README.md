# Typed mixed-app window identity discovery (#2666)

This additive gate addresses the session-setup stop retained in #2499/#2658.
It validates identity evidence before any transition or input.

The gate is deliberately model-free and input-free. It does not run the
four-transition mixed-app allocation or claim task-effect correctness.

A record is admitted only when each expected application has exactly one
selected identity with a non-empty typed window id, matching display, stable
process identity, and a repeat observation with the same identity. Missing,
ambiguous, duplicate, wrong-display, or unstable records yield.

The next live runner must provide raw X11 enumeration and process receipts;
this contract does not manufacture them.
