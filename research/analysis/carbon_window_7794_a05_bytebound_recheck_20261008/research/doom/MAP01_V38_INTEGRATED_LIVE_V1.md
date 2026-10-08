# MAP01 v38 integrated live first outcome

The frozen `map01-v38-integrated-threat-live-01` allocation ran once from the
same enemy-visible MAP01 fixture as v32, with Luna-low, six decision turns and
an advancing game. It completed without retry. The independent scorer found
zero kills, zero deaths, no map exit and an unfinished episode after 31.731s
of control time. Model wall time was 27.489s. This is an interface integration
exposure, not a clear attempt or evidence of faster play than v32: the episodes
are stochastic and the conditions are not a causal speed comparison.

The preregistered audit passes. It reconciles all 119 exact and early typed
observations, every planner/final-admission receipt, seven accepted programs
(six cover, one model plan) with seven verified empty releases, the active
program's compiled steps/SHA/intent token and the independent score. The one
admitted decision created a `running-action-v3` receipt with exact program
binding and closed in `COMPLETED`. No natural mid-action health/ammo revocation
occurred, so the early physical-release/two-phase-cancel path remains
unexposed in this run. The report's formal pass must not be read as a claim
that a real running action was cancelled under threat.

| Final admission | Decisions | Model plan admissions |
|---|---:|---:|
| `INPUT_ADMITTED` | 1 | 1 |
| `REJECTED_ACTION_NOT_CURRENT` | 1 | 0 |
| `REJECTED_POLICY_INVALIDATED` | 4 | 0 |

Decision0 accepted one schema-v6 model plan. Decision1 returned an eligible
active answer, but immediate fresh action validity rejected its predicate
before Executor input. After that rejection, `reusable_cover()` dropped the
model-authored cover. Decisions2–5 had an empty, unauthored coast cover;
their runtime default `maximum_health_loss=0` set each hard minimum to its
current source health (85, 79, 78, 74). Even one point of loss invalidated
this empty cover and interrupted the pending model answer. Six cover programs
were accepted, but there were zero cover renewals and only one of six model
plans ran. This changed-condition retest shows that the construction-tested
integrated path works, while the empty-cover default guard and renewal are
the practical liveness bottleneck.

The next architecture experiment should isolate that bottleneck without
loosening an authored lease from unchanged health. Freeze a distinct
empty-cover condition before model calls: do not treat damage to unauthored
coast as invalidation of a model-authored policy. Preserve health/ammo
observation and fresh immediate action validity, then measure answer
completion, admitted-action fraction, time without useful control and
independent score against the retained v38 baseline. An explicit short
recovery cover can be tested later under its own condition.
Interruption and release tests should be separately designed to expose a
running active program to typed health/ammo changes; absence of a natural
revocation here is a coverage gap. A cross-domain benchmark remains necessary
to keep MAP01 from dominating interface choices.

The first raw output was copied into
[`retained result`](results/map01-v38-integrated-threat-live-01/report.json)
with a file-level manifest of 265 files/41,480,362 bytes. The retained audit
passes independently on Windows and WSL. See the
[`frozen preregistration`](map01_v38_integrated_live_v1_prereg.json),
[`original audit`](audit_map01_v38_integrated_live_v1.py) and
[`retained audit`](audit_map01_v38_retained_v1.py). Interrupted-turn model usage
is incomplete, so no six-turn total-token claim is made.
