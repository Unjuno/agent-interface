# #4258 cost/selectivity predicate ordering v1 — frozen plan

Allocation: `cost-predicate-order-4258-20260923-01`.
Base main: `91b666fa4951ecac35f70f04da7ea504fdbd9604`.

## H
For fixed three-valued short-circuit AND/OR semantics, an order frozen from development decisive-frequency/cost can reduce held-out whole-decision predicate cost relative to authored NAIVE_ORDER without changing TRUE/FALSE/UNKNOWN outcomes.

## T
Four deterministic predicates A/B/C/D with synthetic cost units 1/2/5/10. NAIVE_ORDER is D,C,B,A. Development rows are separate from evaluation and freeze one order per expression using decisive-outcome frequency divided by cost: FALSE frequency for AND, TRUE frequency for OR. Evaluation has 200 weighted rows total and includes cheap-decisive, shifted B-decisive, mid, expensive-required, UNKNOWN-only, UNKNOWN followed by safe decisive short-circuit, and late-UNKNOWN blocks. No online learning or formal tuning.

Three-valued semantics: AND returns FALSE as soon as any FALSE is evaluated, OR returns TRUE as soon as any TRUE is evaluated; otherwise UNKNOWN is retained if any evaluated predicate is UNKNOWN; only an all-known nondecisive path returns TRUE for AND / FALSE for OR. This semantics is order-independent and independently audited.

## D
`PASS_COST_BASED_PREDICATE_ORDERING_SCOPED` iff optimized and naive decisions exactly match full-expression truth including UNKNOWN on every row, optimized weighted cost is strictly lower, and optimized p95 cost is <= naive p95. Any semantic mismatch => `FAIL_SHORT_CIRCUIT_SEMANTICS`; UNKNOWN mismatch => `FAIL_UNKNOWN_MISHANDLING`; otherwise no cost advantage => `HOLD_NO_COST_ADVANTAGE`. Missing frozen costs/selectivity => STOP.

## C
Sequential evaluation only; parallel/asynchronous launch can dominate. Costs are deterministic synthetic units, not hardware/model latency. Selectivity shift is finite and authored, not a population estimate.

## U
No GUI/input/model/provider/network, authority, token, task-quality or production claim.
