# Issue #4186 preformal plan

Allocation: `effect-commit-deadline-4186-20260923-01`.

## H
A deadline checked only before dispatch cannot establish an effect-by-deadline contract when application processing delays the commit. A posthoc check can detect lateness but cannot prevent the already-committed effect. An application-side precommit check of the same absolute 120 ms deadline should refuse directed late commits while preserving on-time effects.

## T
Policies: PRE_DISPATCH_ONLY, POSTHOC_EFFECT_CHECK, APP_COMMIT_DEADLINE. Schedules: EARLY_SHORT ready20+queue10+processing20 ms; NEAR_SHORT 60+10+20; EARLY_LONG 20+10+110; NEAR_LONG 60+10+80. Deadline120 ms; independent freshness400 ms; same CLOCK_MONOTONIC domain. Three repetitions/cell =36 fresh application subprocesses. No model, GUI/input or experiment network. Construction-01 is excluded12/12 and passed the same semantic table.

## D
PASS_EFFECT_COMMIT_DEADLINE_SCOPED requires all36 rows and exact source/process/timing identity; every proposal/predispatch <=120ms; short schedules effect <=120ms under all policies; PRE_DISPATCH_ONLY and POSTHOC produce all 12 long effects after120ms; POSTHOC labels those six LATE only after effect; APP_COMMIT_DEADLINE refuses all six long commits with effect_committed=false/effect_ns=null; authority false; raw-only audit errors=[]; >=10 corruption controls reject. No formal retry/replacement/exclusion/pooling/tuning.

## C
Cooperative application understands the deadline; sleep delay is directed. This does not prove arbitrary-app commit hooks or external-sink atomicity.

## U
No universal/hard-real-time deadline, production authority, crash/power-loss semantics, model/task utility, GUI, token/latency benefit or natural failure rate.
