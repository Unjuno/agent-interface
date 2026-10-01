# Issue #6243 T0 successor-02 — formal result

This additive successor is separate from predecessor allocation
20261002-01, whose one-shot Docker result is FAIL_AUDIT_GATE because its
equal-method-null fixture was not null. That predecessor and its evidence
remain unchanged.

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

Formal candidate and auditor invocations: **1/1**, retries **0**. Both exited
0 inside the pinned, network-disabled, CPU/memory/PID-limited OrbStack Docker
container. The independent raw-only auditor returned METHOD_PASS_SCOPED,
reconstructed 24 attempts across four scenarios with no errors, and rejected
all four frozen mutation controls. The exact command, container configuration,
raw outputs and source hashes are in formal-01/.

This is a synthetic accounting-method validation only. Fixture times, shortcut
selection, acquisition charge, failures and unfinished penalties are designed
values, not human or agent observations. The result does not establish coder
reliability with people, human/agent tempo, GUI performance, causal effects,
population effects, product performance or external validity. See PLAN.md for
H/T/D/C/U and the preregistered gates.

Read PLAN.md for H/T/D/C/U, gates and limitations. No human, GUI, causal,
population, or product claim is supported.
