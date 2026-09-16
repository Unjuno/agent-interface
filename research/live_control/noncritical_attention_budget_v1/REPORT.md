# Noncritical attention budget with critical-event breakthrough

Decision: **PASS_NONCRITICAL_ATTENTION_BUDGET_SCOPED**

Task: `EVENT-NONCRITICAL-ATTENTION-BUDGET-20260917-003`  
Issue: #720  
Immutable publication BASE: `586a288364bc1875f16d0e612e7c1d22867b9889`

## Question

With barrier-aware progress coalescing and extrema-derived `NEEDS_DECISION` held fixed, can planner-facing ordinary progress be capped without suppressing correctness-relevant events?

Frozen budget: **2 noncritical interrupts per `(session, program_id)`**.

## Container-first method

- `py_compile`: PASS
- construction unit tests: **10/10 PASS**
- formal runner: **1 invocation**
- formal reruns: **0**
- deterministic verifier: **PASS_VERIFY**
- post-result source SHA-256 recheck: **7/7 exact**

## Result

The `budget_all_interrupts` negative control exhausted its two slots on ordinary progress and then suppressed required planner interrupts. Across the frozen cases it suppressed:

`TARGET_LOST`, `NEEDS_DECISION`, `TARGET_LOST`, `LEASE_EXPIRED`, `GOAL_REACHED`.

The `noncritical_only_budget` candidate:

- delivers at most **2** ordinary progress interrupts per scope;
- retains a third suppressed progress summary as `latest_noncritical` (seq 3);
- delivers `TARGET_LOST` after budget exhaustion;
- delivers extrema-derived `NEEDS_DECISION` after budget exhaustion;
- delivers `TARGET_LOST -> LEASE_EXPIRED` independently and in exact identity/order;
- delivers required `GOAL_REACHED` after budget exhaustion;
- critical/required breakthrough does **not** increment or reset the noncritical counter;
- keeps session A/B budgets isolated.

All **8/8 frozen gates** are true.

## Interpretation

A finite attention budget is safe only when its scope is explicitly noncritical. Treating every planner interruption as consuming the same quota can convert an attention optimization into correctness loss. Suppressed ordinary progress must remain locally represented rather than being silently forgotten.

## Boundary

This is a deterministic classification/scheduling fixture. Budget=2 is diagnostic, not a production recommendation. It does not establish model/token savings, planner-boundary savings, natural watcher rates, simultaneous-event priority, batching, delivery latency, classification quality, or task success. No task input or authority is granted by this mechanism.
