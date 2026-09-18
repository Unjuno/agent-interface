# #1920 retained Chromium two-tier applicability

Decision: **PASS_LIVE_TWO_TIER_APPLICABILITY_PARTIAL_SCOPED**.

## What the retained live allocation already proves
The audit binds the exact `adaptive_semantic_repair_live_v2.py` source blob
`365184d72a44d71c439e7f03fa7f59c773cffad8` and both retained case reports.

Both live cases use the unchanged adaptive caller v3 reuse route:

| case | repair | final exact sequence | binding | execute | outcome |
|---|---|---:|---|---|---|
| local | local | 13 | CURRENT_EXACT | completed | TASK_SUCCEEDED |
| model | model_reacquisition | 19 | CURRENT_EXACT | completed | TASK_SUCCEEDED |

In both cases, `final_revalidate` takes a new `adaptive-final-current` exact observation, resolves the target against that observation, verifies focus samples match, scores the current target binding, and returns `revalidated` only for the pre-action state expected by the program. The sole execute stage follows this gate.

This is real retained Chromium/X11 evidence for the **fresh final-gate side** of the #1835/#1848 two-tier contract.

## What it does not prove
The same source implements `reuse_revalidate` as a hard-coded `association_changed` response after the old contract is already known invalid. The retained case reports contain zero `PREPARED_REUSABLE_VERSIONED` and zero `PERSIST_DEPENDENCY` role-schema records.

Therefore these runs do not contain the persistent reusable dependency receipt required by #1858/#1900. They cannot be reinterpreted as a full bridge PASS.

## Consequence
The remaining empirical gap is narrower than before:

- caller control-flow dominance: proved by #1916;
- fresh final gate in a real retained caller session: present here;
- persistent reusable role receipt entering `reuse_revalidate` in the same caller session: **still missing**;
- executable #1900 role bridge: still `HOLD_SOURCE_TRANSPORT`.

A next live or retained-data successor should add only the missing reusable dependency receipt at reuse revalidation while leaving the already-proven final gate and caller topology unchanged.

## Limits
Posthoc compatibility only. The role schema did not exist when this live allocation ran, so the final-gate mapping is semantic rather than schema-native. No new task execution, rate, latency, token, reliability, or production claim is made.
