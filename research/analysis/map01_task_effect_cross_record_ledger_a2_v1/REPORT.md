# MAP01 task-effect cross-record ledger A2

Issue #1859. Fresh successor to #1839's retained postformal `FAIL_EFFECT_EVIDENCE_LAUNDERING`. #1839 remains immutable and is not relabeled.

Decision: **PASS_MAP01_TASK_EFFECT_CROSS_RECORD_LEDGER_SCOPED**.

## What changed
Only one factor was added above #1839's record roles: append-only cross-record referential integrity.

A TASK_EFFECT is accepted only when:
- exactly one prior PHYSICAL_ACTUATION matches plan_id + actuation_id;
- effect_id is globally fresh;
- scorer_id resolves to one prior independent/no-authority scorer attestation whose producer differs from controller/actuator producer;
- effect clock is either the actuation clock or is mapped to it by one prior measured clock-map receipt;
- transformed effect time is not before the physical-down upper bound;
- scored=true and input/semantic authority remain false.

STATE_FEEDBACK remains noncausal/no-authority. Missing qualifying task effect remains unresolved/rejected.

## Construction
Excluded construction:20,000 generated ledgers +12 directed controls.
- candidate/oracle mismatch0;
- fixed controls12/12;
- weak TASK_EFFECT acceptance0;
- STATE_FEEDBACK promotion0;
- corruption6/6 rejected.

Construction is not pooled into formal.

## Formal first outcome
Source bundle was frozen/read back before formal. One fresh-seed formal:
- rows: **200,000**
- candidate/oracle mismatch: **0**
- fixed controls: **12/12**
- negative TASK_EFFECT acceptances: **0**
- STATE_FEEDBACK promotions: **0**
- valid same-clock TASK_EFFECT:12,527
- valid measured cross-clock TASK_EFFECT:12,396
- ghost actuation accepted:0
- duplicate effect accepted:0
- duplicate actuation ambiguity accepted:0
- missing/untrusted scorer accepted:0
- unmapped/unmeasured/wrong clock relation accepted:0
- pre-physical-down effect accepted:0
- mismatched lineage accepted:0
- unscored/authority-escalating effect accepted:0

Ordered formal digest:
`cc4713a05175978c01619d3fdcf60632139bf0bcc516d983dec64e1de830229b`.

Formal RESULT SHA-256:
`6572a37a8e3f3f4d3697ad14301f346290a3177654ab6aed8ca1903767785bcc`.

Independent audit errors[]; corruption controls6/6 reject.

Formal1 / reruns0 / replacements0 / tuning0.

## Interpretation
This closes the specific ledger-integrity defects exposed after #1839. It does **not** turn temporal succession into gameplay causality by itself. A future live MAP01 implementation still needs a genuinely independent domain scorer, one comparable monotonic clock/validated clock map, and a fresh allocation that records these receipts without changing control policy.

Old v38/v39 remain unable to supply the missing endpoint posthoc. No gameplay efficacy, survival, latency, token or human-tempo claim follows.
