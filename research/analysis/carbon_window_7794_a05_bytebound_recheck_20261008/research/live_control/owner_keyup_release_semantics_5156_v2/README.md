# Owner key-up release classification v2

This is a host-only protocol-construction experiment for Issue #5156. It
separates explicit client `up` requests, whose owner-thread timing must nest
inside that request's caller bracket, from autonomous cleanup, which must not
be assigned a fabricated caller interval.

The code validates a proposed receipt schema only. It does not import or run
InputOwner, open an X connection, send input, modify shared runtime, or prove
real XSync/key-up behavior. The one-shot tests and separate seeded reference
audit are described in `PLAN.md` and frozen by `FREEZE.json`.
