# Issue #4195 — separate effect-owner deadline boundary

## Disposition

`PASS_EFFECT_OWNER_DEADLINE_SCOPED` for fresh allocation `effect-owner-deadline-4195-20260923-02`.

The predecessor allocation-01 remains `STOP_EXTERNAL_EXECUTION_TIMEOUT` and contributes zero rows. Allocation-02 changed only serialization/execution shape: the unchanged 36-case scientific matrix was prospectively partitioned into twelve immutable 3-case slices after a 3/3 excluded construction slice demonstrated the tool envelope.

## H/T/D/C/U

H: an application-side on-time deadline check before IPC does not establish an effect-by-deadline contract if a separate effect owner can delay commit. A sink-side precommit check against the same absolute deadline should prevent the selected late effects.

T: three policies x four directed schedules x three repetitions = 36 fresh app+sink process pairs. Deadline 120 ms, independent freshness 400 ms, same CLOCK_MONOTONIC domain. The sink alone creates the O_EXCL/fsynced effect file. Formal partition: 12 slices x 3 policies, one invocation each, no rerun/replacement/tuning. No GUI/model/input/network.

D: all 36 rows and all 12 slice terminal outcomes are present. APP_CHECK_ONLY and SINK_POSTHOC_CHECK create six on-time short effects and six late long effects each. SINK_POSTHOC_CHECK labels all six long effects LATE only after commit. SINK_PRECOMMIT_DEADLINE creates six on-time short effects and refuses all six long commits with no effect file. Raw-only aggregate audit errors=[]; 12/12 coherent corruption controls reject; source hashes remain frozen.

C: cooperative local sink receives the same deadline. fsync return is the fixture commit point, not power-loss durability. Directed sleeps expose the contract boundary rather than estimating a natural frequency.

U: no distributed/network service, arbitrary GUI transaction, authentication, hard-real-time guarantee, crash/power-loss atomicity, model/task/token/latency benefit, natural-rate estimate or production promotion.

## Result table

| Policy | short schedules | long schedules |
|---|---|---|
| APP_CHECK_ONLY | 6/6 on-time effect | 6/6 late effect committed |
| SINK_POSTHOC_CHECK | 6/6 on-time effect | 6/6 late effect committed, then labelled LATE |
| SINK_PRECOMMIT_DEADLINE | 6/6 on-time effect | 6/6 refused before effect |

The integration constraint is narrow: if task semantics require the effect itself before an absolute deadline, a check before handing work to another effect owner is insufficient; the owner/transaction boundary that can commit the effect must enforce the predicate before commit. A posthoc late receipt is evidence of a violation, not prevention.
