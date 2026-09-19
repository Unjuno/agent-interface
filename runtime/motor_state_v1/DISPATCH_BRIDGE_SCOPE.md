# Explicit-context dispatch bridge (successor #2530)

This additive module maps a synthetic native dispatch result plus explicit
caller-owned observation/surface/frame context into the existing pure
runtime/motor_state_v1 validator.

The gate is construction-only. It makes no backend, GUI, input, model,
network, authority, or task-effect call. Missing or invalid context fails
closed; rejected/failed/released results remain visible in the report and are
not promoted to accepted MotorState. A passing test is not evidence of live
native-session emission or task success.