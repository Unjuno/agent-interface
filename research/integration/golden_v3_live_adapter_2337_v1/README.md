# Golden v3 live-adapter source pin successor (#2337)

This additive successor closes one integrity gap before any live allocation: the
preflight pins the actual `runtime/cli_v1/golden_v3.py` adapter implementation in
addition to the launcher, API, and retained report. It fails closed on any blob
mismatch and separately holds when live model authority is absent.

The preflight performs no model, GUI, input, network, or task action. A
`READY_FOR_SEPARATE_LIVE_ALLOCATION` result is only a source/authority readiness
signal; it is not a live-task result.
