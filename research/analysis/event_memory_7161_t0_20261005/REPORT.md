# Issue #7161 T0 — bounded method result

**PASS_METHOD_SCOPED.** Five distinct action histories that all end in the same synthetic `dialog_closed` visual state were projected to `NOT_RUN`, `PENDING`, `SUCCESS`, `SUCCESS_THEN_REVERTED`, and `FAILED`. Prediction records stayed separate from effect observations, receipt provenance was checked, input authority remained false, and the independent auditor rejected all three output mutations.

This establishes only the finite typed-history contract in this fixture. It does not show that event-centric memory improves a real agent's continuation/recovery, beats ordinary resumption packets, or is suitable for GUI authority. Raw fixture, scripts, outputs, exact commands, source freeze, and hashes accompany this report.
