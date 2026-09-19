# Anytime fidelity typed admission R0 — plan

Parent: GitHub Issue #1662. Successor Issue: #1796.
Task: `ANYTIME-FIDELITY-TYPED-ADMISSION-R0-20260919-001`.
Base: `c92c985b34a351cbcc12eb6b0d68eb2a14b3c7e3`.
Additive publication path: `research/analysis/anytime_fidelity_typed_admission_r0_v1/**`.

## Question

Can an anytime observation/verification scheduler safely choose the single highest scalar fidelity that fits the apparent source-validity slack, or must admission account separately for task-required evidence roles and downstream time reserve?

## H

A scalar highest-fitting rule is insufficient in the frozen catalog for two independent reasons.

1. Evidence coverage is not totally ordered. `TEMPORAL` and `VERIFY` have equal cost but cover different evidence roles.
2. Observation/verification compute is not the terminal operation. A variant that consumes the entire apparent validity slack can finish too late to leave the required downstream guard/commit/verification reserve.

A typed selector that checks both evidence coverage and downstream reserve before selection should make zero unsafe admissions over the frozen finite state space.

## Frozen catalog

Synthetic time units are dimensionless test units, not milliseconds.

| variant | bounded cost | evidence roles |
|---|---:|---|
| CURRENT | 1 | CURRENT |
| TEMPORAL | 3 | CURRENT, TEMPORAL |
| VERIFY | 3 | CURRENT, VERIFY |
| FULL | 6 | CURRENT, TEMPORAL, VERIFY |

Fixed scalar order for the negative controls: `CURRENT < TEMPORAL < VERIFY < FULL`.

The key same-cost incomparability is intentional: `TEMPORAL` contains evidence not present in `VERIFY`, while `VERIFY` contains evidence not present in `TEMPORAL`.

## Frozen state space

- validity slack: integers 0..10 synthetic time units;
- downstream reserve: integers 0..4 synthetic time units;
- required evidence: every nonempty subset of {CURRENT, TEMPORAL, VERIFY}.

Total states: 11 × 5 × 7 = 385.

## Safety definition

A selected variant is safe only when:

- every required evidence role is covered by that variant; and
- bounded variant cost plus downstream reserve does not exceed current validity slack.

`DEFER` is always safe but may be unnecessarily conservative when some safe variant exists.

## Policies

1. `SCALAR_RAW_HIGHEST`: choose the highest scalar-ranked variant whose variant cost alone fits raw validity slack.
2. `SCALAR_RESERVED_HIGHEST`: reserve downstream time first, then choose the highest scalar-ranked fitting variant; no evidence-role search.
3. `SCALAR_RESERVED_POSTCHECK`: same scalar choice as (2), but if the chosen variant does not cover the required evidence, fail closed to DEFER rather than searching an incomparable alternative.
4. `CURRENT_ONLY`: choose CURRENT only when it both covers the required evidence and leaves downstream reserve; otherwise DEFER.
5. `TYPED_RESERVED`: among variants that both cover required evidence and leave downstream reserve, choose the one with maximal evidence-cardinality, then scalar rank; otherwise DEFER.

The postcheck comparator is an extra negative control: it shows that adding a fail-closed coverage check to a scalar ranking can restore safety while still unnecessarily deferring a state for which an incomparable fitting variant exists.

## T

- analytical witness that TEMPORAL and VERIFY are same-cost incomparable evidence sets;
- one exhaustive formal invocation over all 385 frozen states;
- independently re-derived auditor that does not import candidate policy functions;
- source hash verification against `FREEZE.json`;
- corruption controls mutate one TYPED_RESERVED row decision, one reported catalog evidence set, and one summary count;
- formal invocations: 1; reruns: 0; post-freeze tuning: 0.

## D

PASS only if:

- state count = 385;
- TYPED_RESERVED unsafe admissions = 0 and false deferrals = 0;
- SCALAR_RAW_HIGHEST has at least one deadline-reserve violation and at least one evidence-coverage violation;
- SCALAR_RESERVED_HIGHEST has zero deadline-reserve violations and at least one evidence-coverage violation;
- SCALAR_RESERVED_POSTCHECK has unsafe admissions = 0 but false deferrals > 0;
- CURRENT_ONLY unsafe admissions = 0 and false-defers at least one feasible TEMPORAL-required state and one feasible VERIFY-required state;
- explicit equal-cost TEMPORAL-vs-VERIFY incomparability witnesses exist;
- audit/source integrity and all three corruption controls pass.

Any TYPED_RESERVED unsafe admission => `FAIL_TYPED_FIDELITY_SAFETY`.
If scalar controls unexpectedly have no discriminating failures => `HOLD_NO_FIDELITY_DISCRIMINATOR`.

## C

A scalar preset can be adequate inside a restricted production envelope if variants are genuinely evidence-nested, downstream reserve is explicitly accounted, and monotone utility has been empirically established. This finite result does not establish those conditions.

## U

Synthetic integer cost bounds and authored evidence roles only. No real latency, model quality, token use, GUI/backend transfer, stale probability, energy, or production scheduler claim.
