# C2 — semantic predicate vs exact relevant version

Status: **RETAIN predicate-truth validation at this fixture; exact version is safe but over-strict.**

C2 follows C1 without changing outbox durability, receiver DB, content binding or the receiver-side transaction boundary. Only the plan-bound validity representation changes.

## Frozen cases

Two policies:

- `exact_version`: target resource version must equal the plan-time version;
- `predicate_truth`: authored `action_allowed` truth must equal the plan-time result.

Four schedules, 50 repetitions each/policy = **400 cases**:

1. stable;
2. target version changes, but `action_allowed` remains true (`semantic_same`);
3. target version changes and `action_allowed` becomes false (`predicate_invalid`);
4. unrelated resource changes.

Ground truth: stable, semantic-same and unrelated changes may effect; predicate-invalid must reject.

## Result

| Policy | Cases | Effects | Stale effects | False rejects |
|---|---:|---:|---:|---:|
| exact target version | 200 | 100 | 0 | **50** |
| predicate truth | 200 | 150 | **0** | **0** |

Exact version rejects every semantically preserving target-version change. The plan-bound Boolean predicate preserves those 50 valid effects while still rejecting all 50 predicate-invalidating changes.

Independent audit reports zero errors across 400 retained rows. Corrupt effect count, predicate/context snapshot and sender durable flag are all detected.

Executed source SHA-256:

- `c2_runner.py`: `4e28de5e30998f90f7106788f7bd3e01962063979ad9648d208ba40416f87b02`
- `c2_audit.py`: `74955e687bc88b2ce783e35678fb708a51a8174f5d136c8fc67e2ec66b722513`

## H / T / D / C / U

**H.** Semantic predicate preservation can be more precise than exact resource-version equality for delayed outbox delivery.

**T.** 400 deterministic cases, same receiver-side atomic validation/effect boundary as C1.

**D.** `predicate_truth` PASS at C2: stale 0 / false reject 0. `exact_version` remains sound but produced 50 false rejects.

**C.** Predicate truth alone can still be incomplete: another logical object/context may satisfy the same predicate after a context switch.

**U.** One authored Boolean predicate; no automatic dependency discovery, alias/context identity, network, GUI, crash or replay factor.

## Next smallest rung

C3 holds predicate truth fixed and adds one dependency only: logical context identity. Compare `predicate_only` against `context_identity + predicate` when context A is replaced by context B that still satisfies `action_allowed=true`. Keep stable, predicate-invalid and unrelated controls.
