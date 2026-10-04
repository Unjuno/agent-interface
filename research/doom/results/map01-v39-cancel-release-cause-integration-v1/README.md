# Owner-to-ExecutorV12 cancellation publication integration check

This local construction regression joins the actual `ExecutorV12` implementation to the actual `input_owner_v12` request thread. A minimal backend exercises `release_all` by calling that owner; fake Xlib tracks a held key and confirms its release. The test forces cancellation to become owner-visible only after the explicit release request is dequeued, so the owner must classify the cleanup as `cancelled` while the executor's cancellation check already sees it.

## H / T / D / C / U

- **H:** For the forced post-dequeue/pre-dispatch cancellation interleaving, v12 will record a verified `cancelled` release; `ExecutorV12._publish_release` will publish that lease-bound receipt before the terminal event, and the terminal status will be `cancelled`.
- **T:** Run `python -B research/live_control/test_executor_owner_cancel_cause_v1.py` once on the local Windows host, using real ExecutorV12 and owner code with a deterministic in-process fake-Xlib display. Preserve output and exit status. Run the existing ExecutorV12 unit regression and the independent C02 audit as related checks.
- **D:** PASS if one owner release is verified with no keys/buttons down, the event stream contains `input_released` with reason `cancelled` before a `cancelled` terminal event, and the fake display records a key press followed by key release. Any missing or misordered event, wrong reason, nonempty state, or nonzero test exit is FAIL.
- **C:** This is software-construction evidence with fake Xlib and a minimal backend. It does not instantiate the complete v14 measurement backend or MAP01 session, and it does not demonstrate GUI/game effects, useful task feedback, recovery latency, or a live control benefit. The deferred-visibility event is a deterministic scheduling fixture for the cancellation interleaving.
- **U:** OS/X server scheduling, real XTest behavior, full v14 backend/session composition at runtime, application response, scorer behavior, bounded recovery, and comparative resource use remain unobserved.

## Result

PASS. `INTEGRATION-01.stdout.txt` reports one passing integration test. The existing ExecutorV12 regression reports 2/2 PASS, and C02's 12-check frozen-source/raw/wiring audit remains PASS. The actual event assertions prove `input_released` was published before the cancelled terminal event, linked to an owner record with `reason=cancelled`, `verified=true`, and empty key/button lists. The fake display observed the held key released.

This closes the specific owner-cause to executor-publication construction gap identified in C02's limitation. It does not establish the full MAP01 v14 runner, live environment, or Issue #59 objective. No allocation, server, device, game, model, or formal experiment was used. This is a local regression check, not a frozen formal run.
