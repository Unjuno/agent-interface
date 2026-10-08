# Explicit read-only observation while caller STOP stays sticky

Seed 1001070, one fresh pending allocation. Tk app Save acknowledgment delayed
3000 ms, requested cue wait 1000 ms. Source and host bundle frozen before run.
Primary reviews original initial PNG, mints Save point, requests input once,
reviews original pending PNG and recorded STOP, explicitly asks observeAfterStop,
reviews the later PNG, then closes. The application continues in real time;
no app pause, input replay, polling scheduler, sensor, new model, session restart,
remint, alias renewal or automatic authority recovery. Ordinary observe/input
remain blocked. Host transport/evidence failures still deny even the explicit
read-only call; this is not a reconciliation guarantee for broken transports.
App events independently read only after all owners/children exit. Preserve
failures, commands, response/image hashes and caller state. No latency, token,
cost or human-tempo improvement claim from this functional experiment.
This local candidate is stacked on pending PR #6077; do not reset its queued
checks or publish this branch until the parent integration is resolved.
