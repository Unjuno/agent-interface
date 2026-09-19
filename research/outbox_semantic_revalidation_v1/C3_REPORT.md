# C3 — logical context identity + semantic predicate

Status: **RETAIN context identity + predicate; FAIL predicate-only under context replacement.**

C3 keeps C2's plan-bound predicate validation and adds/omits exactly one dependency: logical context identity.

## Frozen comparison

Policies:

- `predicate_only`: require only plan-time `action_allowed=true`;
- `context_plus_predicate`: require `context_id=A` and `action_allowed=true`.

Schedules: stable; context A replaced by B while predicate remains true; predicate invalidated within A; unrelated state change. Fifty repetitions/policy/schedule = **400 cases**. Receiver validation and effect insertion remain one SQLite transaction.

Ground truth: stable/unrelated may effect; context replacement and predicate invalidation must reject.

## Result

| Policy | Cases | Effects | Wrong-context / stale effects | False rejects |
|---|---:|---:|---:|---:|
| predicate only | 200 | 150 | **50** | 0 |
| context identity + predicate | 200 | 100 | **0** | **0** |

Predicate truth is not sufficient when another logical context satisfies the same predicate. All 50 A→B replacements executed under `predicate_only`; the context-bound arm rejected them while preserving every stable and unrelated-change effect.

Independent audit reports zero errors over 400 rows. Deliberate effect-count, context-ID and sender-durable corruptions are detected.

Executed source SHA-256:

- `c3_runner.py`: `5fd97cbb6ef2cd7e66ae2c80270260e9be301b50c0ee4ad856c3e87f6b0d7afe`
- `c3_audit.py`: `6baa8e3a78699e41fe8d8c05b74e421f07952ba7d79ede6fe6f4554e3686da67`

## Decision

Delayed outbox validity in this fixture now requires at least:

`logical context identity + authored semantic predicate`

Idempotency remains a separate replay property from PR #240.

## Competing explanation / next rung

A context identifier can itself be reused across object incarnations. C4 changes exactly one dimension: context `A` keeps the same public ID but its **generation/incarnation** changes before delivery while `action_allowed=true`. Compare `context_id + predicate` against `context_generation + predicate`. Stable, predicate-invalid and unrelated controls remain fixed.

Do not infer a generic GUI identity scheme from this fixture.
