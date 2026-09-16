# Cross-session critical arbitration under noncritical surface flood

Decision: **PASS_CROSS_SESSION_CRITICAL_ARBITRATION_SCOPED**.

Task: `EVENT-MULTISURFACE-CRITICAL-ARBITRATION-20260917-004`  
Issue: #728  
Publication BASE: `a4538c1edcaa8fb6a9305c303fa76c70561ffed9`

## One-factor question

Hold record classification and strict FIFO within every session fixed. Compare only cross-session delivery arbitration:

- `global_fifo`: oldest global arrival first;
- `critical_head_first`: inspect only each session head; if any head is correctness-relevant, deliver the oldest-arrived critical head, otherwise oldest head overall.

The candidate never skips an earlier record inside one session.

## Container first outcome

- `py_compile`: PASS
- construction unit tests: **10/10 PASS**
- formal runner: **1 invocation**
- formal reruns: **0**
- verifier: **PASS_VERIFY**
- post-result frozen-source rehash: **7/7 exact**

All **8/8** frozen gates are true.

## Results

### Unrelated surface flood

Eight noncritical records from session A precede B:`TARGET_LOST`.

- global FIFO critical delivery slot: **9**
- critical-head-first delivery slot: **1**
- all nine records are still delivered exactly once.

### Critical arrives after partial drain

After three A records have already been delivered, B:`FOCUS_LOST` arrives while five older A noncritical records remain.

- global FIFO B delivery slot: **9**
- candidate B delivery slot: **4** (the next eligible slot)

### Causal/FIFO controls

- same-session B:`PROGRESS` then B:`TARGET_LOST` remains **PROGRESS -> TARGET_LOST**; no within-session overtake;
- simultaneous critical session heads B:`TARGET_LOST`, C:`LEASE_EXPIRED` preserve their global arrival order;
- B:`NEEDS_DECISION` is slot1 under unrelated A noncritical backlog versus slot6 under global FIFO;
- noncritical-only streams have byte-identical delivery order under both policies;
- every record identity is delivered exactly once and each session projection is identical to its input FIFO projection.

## Interpretation

A critical event can bypass an unrelated surface's noncritical backlog without weakening causal ordering if arbitration is restricted to **session heads** and within-session FIFO is an invariant. Global FIFO exposes cross-surface starvation in the authored fixture.

This does not justify arbitrary priority reordering within a session.

## Boundary

Delivery slots are logical, not wall-clock latency. No batching, weighted priorities, deadlines, task-importance weights, preemption of already-running planner work, fairness under endless critical load, real watcher traffic, model benefit, or task-success claim is made.

Full result SHA-256: `a252ac3589bf3cb75ee03b202201e289d5db9fc13feb4cdfc05e53aab82d4ee2`.
