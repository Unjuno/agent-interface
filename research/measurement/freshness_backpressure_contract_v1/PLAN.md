# Freshness Backpressure Critical-Retention Contract v1

TASK: FRESHNESS-BACKPRESSURE-CRITICAL-RETENTION-20260917-001
BASE: c0d4ea7b216853ec74c66a3a03ba7362a264ead4
PARENT: #43

H: latest-plus-critical coalescing can remove superseded fresh noncritical states while retaining every critical edge exactly once/in source order and never presenting stale noncritical state as current.

T: standard-library container only; fixed adversarial controls; independently structured reference reducer; seeded random corpus >=250,000 records; bounded exhaustive short streams. No GUI/model/provider/network/task-input/shared-runtime mutation.

D: candidate/reference exact agreement; 100% critical retention; stale state never current; at most one fresh noncritical per session/target/stream; no cross-scope coalescing; malformed IDs/order fail closed; output authority=false.

C: authored critical allowlist can itself be incomplete; pathological critical storms are not solved by this policy.

U: synthetic queue semantics only; no task/model/token/human-tempo claim.
