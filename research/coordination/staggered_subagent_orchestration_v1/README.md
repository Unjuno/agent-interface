# Condition-based staggered sub-agent orchestration v1

Additive scoped runner for Issue #3158. It retains a six-scenario held-out trace and compares immediate, fixed-delay, condition-based, and serial-critical policies. `CONDITION_STAGGER` requires a typed release condition; elapsed delay alone is never evidence. This is a deterministic orchestration result, not a model-quality or production claim.
