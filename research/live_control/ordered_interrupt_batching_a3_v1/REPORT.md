# Ordered interrupt batching A3 — formal result

Issue #1884, task `EVENT-ORDERED-INTERRUPT-BATCHING-A3-SHARDED-20260919-003`.

## Decision

**`PASS_ORDERED_INTERRUPT_BATCHING_A3_SCOPED`**

A3 changes only formal execution/durability packaging from the timed-out #1876 monolith to nine immutable disjoint shards. The event schema, batch size 4, ordered batching semantics, exhaustive corpus, prefix checks, directed controls and scientific gates are unchanged.

## Formal outcome

- logical formal allocations: **1**; shard process invocations: **9**; reruns/replacements/tuning: **0/0/0**;
- exact corpus coverage: **299,593 sequences / 2,054,353 prefix checks**;
- sequence mismatches: **0**; identity errors: **0**; per-session projection errors: **0**; metadata errors: **0**;
- sequences with fewer logical deliveries than INDIVIDUAL: **299,584**;
- directed negative comparator reversals: **6**;
- malformed controls: **5/5 fail closed**;
- independent audit: **PASS**, errors `[]`;
- postformal source rehash: **exact match**.

The negative `PRIORITY_SORTED_BATCH` comparator reverses causal/order-sensitive directed cases, while `ORDERED_BATCH` preserves the exact scheduler-produced sequence and every per-session projection. The supported conclusion is therefore narrow: after classification/admission/arbitration are already complete, batching may reduce planner-delivery count only if batch membership preserves the scheduler order exactly rather than reprioritizing inside the batch.

## Execution conditions

Python 3.13.5; AMD EPYC 9V74, 5 vCPU under KVM. Shard scientific loop elapsed median **4.626s**, max **4.842s**, sum **41.076s**. Aggregate wrapper 0.70s; independent audit 9.94s. These timings are descriptive packaging measurements, not scientific speed thresholds.

## Integrity / stops

Preformal source transfer mismatches were detected before allocation and removed; final source bundle parts and readable freeze/plan blobs matched exactly. An optional postformal corruption-driver later exceeded its outer wrapper; no formal was rerun, and that diagnostic STOP does not alter the PASS because the independently implemented audit and source rehash had already passed.

## Scope

No claim is made about a model understanding multiple events in one prompt, token savings, wall-clock planner latency, live transport atomicity, ACK/retry semantics, natural event rates, task success or production batch size. A next high-information rung should test planner/model decision fidelity on ordered batches versus individual delivery with identical underlying event sequence and accounting.
