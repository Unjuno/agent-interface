# Issue #6243 T0 successor-02 — construction only

This is a **preparation package**, not a frozen or formal result. It is kept
separate from predecessor allocation 20261002-01, whose one-shot Docker result
is FAIL_AUDIT_GATE because the equal-method-null fixture was not null.

The construction fixture has 12 blinded pairs / 24 attempt rows. Its corrected
equal-method null is exactly 18,000 ms per arm per pair. In the separate
shortcut-mixture fixture, method-specific times are identical across arms:
4,000 ms for shortcut, 10,000 ms ordinary. Natural selection totals are
22,000 ms H and 34,000 ms A over four pairs. Adding a constructed one-time
35,000 ms H acquisition charge yields H/A totals of 57,000/34,000 ms at one
repeat, 123,000/136,000 ms at four, and 255,000/340,000 ms at ten. These are
designed values, not observations.

Host construction checks: Python compilation, JSON parsing, 15 assertions and
4/4 corruption controls passed. Two construction defects and their repairs are
preserved in FAILURE_CONSTRUCTION_01.txt. The candidate/audit files prefixed
CONSTRUCTION are not formal outputs.

Formal candidate and auditor invocations: **0/0**. No container was started.
The exact CPU OrbStack slot is pending explicit release/grant on coordination
issue #5085; two unrelated containers were running at the last read-only
inventory. Cached python:3.12-alpine digest was inspected, but that is not an
allocation. OrbStack's orb CLI is available; the image was read-only inspected,
but no formal container was launched without the slot grant.

Read PLAN.md for H/T/D/C/U, gates and limitations. No human, GUI, causal,
population, or product claim is supported.
