# Final action admission v2

V1 resolves planner terminal state, policy invalidation, controller validation
and the first actual Executor acceptance. V2 inserts one mandatory boundary for
the newly returned action:

```text
planner completed + policy current
  -> READY_FOR_ACTION_VALIDITY
  -> fresh action validity VALID_CURRENT
  -> READY_FOR_FRESH_EXECUTOR_ADMISSION
  -> actual Executor acceptance
  -> INPUT_ADMITTED
```

Any current-state rejection ends as `REJECTED_ACTION_NOT_CURRENT` with no
Executor receipt. Planner/policy and controller no-input paths remain distinct
and cannot bind an action-validity result. A later hard event still revokes
current authority while preserving the historical acceptance.

The final boundary deterministically recomputes the supplied validity receipt
from its exact action, contract and snapshot; a changed action or forged result
is refused. The validity receipt itself never issues input or grants authority. This keeps
the fast local evidence check separate from the Executor, which remains the only
component that can accept a motor program. This is a model-free construction;
it is not integrated into the hash-frozen v32 controller and has no live result.
Any controller integration must use v33 or later.
