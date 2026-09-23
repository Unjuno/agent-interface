# #1318 preformal stack-transport stop

Disposition: `PREFORMAL_SETUP_STOP_STACK_CAPTURE_TRANSPORT_LOST`; scientific disposition **NONE**.

- construction2 / formal0 / reruns0
- control session complete and clean
- V12_EFFECT child again timed out at8s with no science row
- faulthandler was configured for an all-thread dump at5s
- persisted stderr is empty, but the supervisor only retained TimeoutExpired stderr when it was `str`
- pure offline reproduction shows timeout stderr can be `bytes` even with `text=True`; therefore stack presence/absence is not recoverable from #1318
- no effect/physical row is reconstructed
- final process/socket residual0

Next factor is diagnostic transport only: connect child stdout/stderr directly to persistent files before launch. Do not change science runner, timeout, action, scoring, Xvfb lifetime or thresholds.
