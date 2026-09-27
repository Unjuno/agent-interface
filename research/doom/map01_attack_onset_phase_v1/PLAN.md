# MAP01 attack onset phase — Issue #4223 H/T/D/C/U freeze

Origin: successor to #4193 `HOLD_ATTACK_TASK_EFFECT_NOT_REPRODUCED`. No predecessor row is rerun or pooled.

## H
With fixture, seed 992600, v12 physical-edge route, independent scorer, key `space`, and 600 ms attack fixed, attack onset phase may determine whether an independently scored TASK_EFFECT is observed. Compare only 0 ms authored pre-roll (IMMEDIATE) with exactly 600 ms input-free pre-roll (ONE_WINDOW_PREROLL).

## T
Provided Linux x86_64 execution container; CPython 3.13.5; private Xvfb/Openbox; artifact 10398313098 SHA-256 `522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b`; runtime base `9e6d5ecdbb5440fd5df1883161f2c63b2c3bb245`; ViZDoom1.3.0, ASYNC_SPECTATOR35Hz, skill1, `map01-threat-contact-v2`. InputOwner-v12 bundle SHA-256 `5960543c9d9193b5615da2b545eb7a385a4d2e17bfe12513731bf9e92f948422`.

Excluded construction: one matched pair only, both physical edge/release exact, both TASK_EFFECT0. No formal result consumed.

Formal schedule: 4 pairs / 8 fresh restored sessions, counterorder I-P / P-I / I-P / P-I. Every session seed992600. Both arms issue exactly one `space` hold600ms; PREROLL adds only input-free sleep600ms after initial observation and before clock/admission. Exactly one formal orchestration; reruns/replacements/tuning0.

The retained scorer exposes monotonic `sample_ns` chronology but no game-tic field; no tic is inferred.

## D
`PASS_ATTACK_ONSET_PHASE_DISCRIMINATES_SCOPED` iff source/process/physical/release/integrity gates pass for all8 and the boolean presence of an independently bound TASK_EFFECT differs between arms in at least3/4 matched pairs. Otherwise, with integrity intact, `HOLD_ATTACK_ONSET_PHASE_NOT_DISCRIMINATING`. No further delay/seed/duration sweep follows a HOLD.

FAIL on wrong arm delay, wrong seed, wrong actuation/lineage, scorer authority escalation, effect before physical DOWN, duplicate effect, non-neutral release, missing source/process evidence, or candidate/auditor disagreement.

## C
Wall-clock pre-roll is a proxy for internal asynchronous game/AI/render phase. A discriminator is fixed-fixture onset evidence, not a general attack policy.

## U
No recovery-vs-coast efficacy, MAP01 clear, model quality, token/latency, population reliability, human-tempo or production claim.

## Variable table

| field | meaning | SI unit | definition | domain/assumption | type |
|---|---|---|---|---|---|
| `d_pre` | authored pre-roll | s | 0 or 0.600 | sole formal factor | scalar |
| `d_attack` | attack hold | s | exactly 0.600 | fixed | scalar |
| `sample_ns` | independent scorer timestamp | s (stored ns) | monotonic scorer sample | evaluator-only | scalar integer |
| `t_down` | physical DOWN interval | s (stored ns) | v12 X-server bracket | ordered interval | integer pair |
| `N` | formal sessions | 1 | 4 pairs × 2 arms | exactly8 | scalar integer |

Dimensional check: delays and monotonic timestamps are time; counts/identities are dimensionless and are never added to time.
