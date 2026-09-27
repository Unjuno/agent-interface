# MAP01 task-effect instrumentation contract

Successor work for Issue #1839. H/T/D/C/U are recorded in Issue #1839 and PR history.

The validator keeps PHYSICAL_ACTUATION, STATE_FEEDBACK, and TASK_EFFECT distinct. Only independently scored, plan/actuation-bound effects on a comparable integer monotonic clock can be classified as TASK_EFFECT. Missing effects remain unresolved; no authority is granted.

The test suite contains one positive and seven refusal/negative controls, including viewport/state/terminal laundering, unbound and early effects, duplicate identity, and non-authoritative clock metadata. Old v38/v39 evidence is not used as a positive denominator. This is offline contract/readiness evidence only and does not authorize a live MAP01 allocation.
