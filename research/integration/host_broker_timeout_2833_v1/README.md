# Host broker timeout diagnosis (#2833)

The broker now applies a bounded subprocess timeout and preserves command,
request, timeout, stderr, and monotonic start/exit evidence. A local no-GUI
diagnostic with `HOST_MODEL_BROKER_TIMEOUT_S=5` terminated deterministically
with `HOST_BROKER_SUBPROCESS_TIMEOUT`; the response file remained empty and
authority stayed false.

This identifies the wait boundary but does not establish model compatibility,
GUI effects, or task-route readiness.

