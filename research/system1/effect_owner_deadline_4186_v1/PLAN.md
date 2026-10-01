# Issue #4195 preformal plan

Allocation: `effect-owner-deadline-4195-20260923-01`.

## H
An application-side deadline check before IPC cannot establish effect-by-deadline when a separate effect owner can delay commit. APP_CHECK_ONLY and SINK_POSTHOC_CHECK should expose late effect files; SINK_PRECOMMIT_DEADLINE should refuse those writes while preserving valid short effects.

## T
Three policies: APP_CHECK_ONLY, SINK_POSTHOC_CHECK, SINK_PRECOMMIT_DEADLINE. Four schedules: EARLY_SHORT 20+10+20 ms, NEAR_SHORT 60+10+20, EARLY_LONG 20+10+110, NEAR_LONG 60+10+80. Deadline120 ms; independent freshness400 ms; same CLOCK_MONOTONIC domain. Three repetitions per cell =36 fresh app+sink process pairs. Sink alone writes an O_EXCL fsynced effect file. No model, GUI/input, experiment network or user data. Construction-01 is excluded12/12 PASS.

## D
PASS_EFFECT_OWNER_DEADLINE_SCOPED requires all36 rows; proposal/predispatch/app-check <=120ms; all short schedules create exactly one on-time effect file under all policies; APP_CHECK_ONLY and SINK_POSTHOC_CHECK create all12 long effect files after120ms, with posthoc LATE in its six cases; SINK_PRECOMMIT_DEADLINE refuses all six long writes with no effect file; file/receipt case_id,sink_pid,effect_ns match; app/sink exits0; authority false; raw-only audit errors=[]; >=10 coherent corruptions reject. No formal retry/replacement/exclusion/pooling/tuning.

## C
Cooperative sink receives the deadline; fsync return is the fixture commit point, not power-loss durability. IPC/sleep timings are directed.

## U
No distributed/network service, arbitrary GUI transaction, hard-real-time, authentication, model/task/token/latency benefit, natural failure rate, or production promotion.
