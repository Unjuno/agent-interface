# C4 — same-ID context replacement / incarnation token

Status: **RETAIN authoritative context incarnation + semantic predicate; FAIL public context ID + predicate under ID reuse.**

C4 holds the public context ID and semantic predicate fixed while changing only the underlying context incarnation/generation.

## Frozen comparison

Policies:

- `id_plus_predicate`: require public `context_id=A` and `action_allowed=true`;
- `generation_plus_predicate`: additionally require the plan-time context generation/incarnation.

Schedules: stable; same public ID `A` replaced by generation 1 while predicate remains true; predicate invalidation in generation 0; unrelated state change. Fifty repetitions/policy/schedule = **400 cases**.

Ground truth: stable/unrelated effect; same-ID replacement and predicate invalidation reject.

## Result

| Policy | Cases | Effects | Wrong-incarnation / stale effects | False rejects |
|---|---:|---:|---:|---:|
| context ID + predicate | 200 | 150 | **50** | 0 |
| context generation + predicate | 200 | 100 | **0** | **0** |

A stable-looking public identifier is insufficient when it can refer to a new incarnation. Generation/incarnation evidence closes this targeted replacement case without coupling to unrelated changes.

Independent audit reports zero errors across 400 rows; deliberate effect-count, generation snapshot and sender-durable corruptions are detected.

Executed source SHA-256:

- `c4_runner.py`: `51a3e1575f453dc31dde22061f1b9be02c2d41638ae19f64e70c034e2ff8bd6a`
- `c4_audit.py`: `2378f9cc1a4cd5358c7702117443f2c9016f538baf8a1965dfbe737d9edbd3f2`

## Decision

For the delayed-receiver fixture, the narrow retained validity envelope is:

`authoritative context incarnation + authored semantic predicate`

This complements, rather than replaces, PR #240's receiver idempotency and sender outbox durability.

## Limit

The generation token is authoritative by fixture construction. Arbitrary GUI applications may not expose an equivalent incarnation or effect-commit boundary. The next useful step is transfer to one existing real application with an authoritative version/incarnation, not another synthetic scalar field.
