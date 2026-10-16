# Executor v11 attestation with established cancellation identity

The first pre-artifact live allocation exposed a composition bug in Executor
v10. It copied the v3 lifecycle but defined new `Cancelled` and
`DecisionRequired` classes. Existing backends raise the established v3 classes,
so v10's generic exception branch converted a matched cancellation into a
`failed / Cancelled()` terminal.

Executor v11 subclasses Executor v3 and imports its exception classes. It
overrides only admission: after deep-copying and validating the whole program it
adds the same canonical program SHA-256 used by v10. Execution, cancellation,
terminal status and release remain the v3 implementation. A focused control
raises `executor_v3.Cancelled` from the backend and reaches an exact `cancelled`
terminal with verified release.

This model-free repair does not change or reinterpret the frozen v10 failure.
It proves exception compatibility in the test double, not live cancellation
latency or task correctness.
