# Issue #4193 — live MAP01 v12 attack -> TASK_EFFECT H/T/D/C/U

## H
One fixed 600 ms `space` actuation in the immutable `map01-threat-contact-v2` exposure at seed 992600 can carry exact v12 physical DOWN/UP lineage and an independently sampled positive TASK_EFFECT (`KILL_COUNT_INCREASE` or `MAP_EXIT`) on the same monotonic process clock. NO_INPUT must not fabricate actuation or bound effect.

## T
Immutable offline artifact 10398313098 / SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`; CPython 3.13.5; ViZDoom 1.3.0; private Xvfb/Openbox; exact fixture; timeout 60 s; v12 input owner SHA-256 `b63e8a925a5ff741385fb69b8cf20ac07e01a520f34607778d8d28a0256c1508`; adapter SHA-256 `ed7e4f00675e79a9ef86984c7c129bb6c3eda64855c6c71821c313c9feb9badf`.

One excluded setup pair only. Formal after GitHub source freeze: 3 matched pairs / 6 fresh restored sessions, order NO_INPUT→ATTACK, ATTACK→NO_INPUT, NO_INPUT→ATTACK. Same seed 992600 each time. No model/provider/adaptation/retry/window tuning.

## D
PASS only if all 3 ATTACK sessions have one confirmed physical DOWN and UP for `space`, neutral verified release, stable actuation lineage, exactly one positive bound TASK_EFFECT each, while all 3 NO_INPUT sessions have no task actuation and no positive event. Clean physical lineage with 0/3 effects is `HOLD_ATTACK_TASK_EFFECT_NOT_REPRODUCED`; any NO_INPUT positive is `HOLD_EFFECT_NOT_ACTION_DISCRIMINATING`; false binding/authority escalation is FAIL.

## C
Repeated restores of one seed are not independent maps. A positive sample is endpoint-composition evidence, not recovery-vs-coast efficacy, survival, model benefit, or MAP01 clear.

## U
Whether the retained development one-kill exposure transfers to this exact v12 measurement path is unknown. The excluded setup observed clean physical edges but no positive effect and does not alter the frozen seed, interval, scorer, or formal denominator.

## Variable table

| field | meaning | SI unit | definition | domain / assumption | type |
|---|---|---|---|---|---|
| `sample_ns` | scorer observation time | s (stored ns) | same-process monotonic timestamp | nonnegative; comparable only in session | integer scalar |
| `physical_down_interval` | physical key-down censor bracket | s (stored ns) | v12 pre/post keymap sample interval | ordered two-endpoint interval | integer pair |
| `physical_up_interval` | physical key-up censor bracket | s (stored ns) | v12 pre/post keymap sample interval | ordered two-endpoint interval | integer pair |
| `kill_count` | independent kill counter | 1 | ViZDoom scorer state | nonnegative integer | integer scalar |
| `N` | formal sessions | 1 | 3 pairs × 2 arms | exactly 6 | integer scalar |

Dimensional check: ordering compares only monotonic timestamps in ns from the same process/session. Counts are dimensionless and are never arithmetically mixed with time.
