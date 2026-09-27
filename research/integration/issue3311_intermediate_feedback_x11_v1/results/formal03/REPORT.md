# Formal allocation 03: compiled-interface contract STOP

The explicit container entrypoint and expanded 512-PID/2-GiB limits allowed
the runner, Xvfb, local fixture server and Chromium to start. The existing
compiled runtime then rejected the constructed interface before its first
observation because its requested `max_runtime_ms=15000` exceeded the runtime's
10,000-ms schema limit.

**Disposition: `STOP_INTERFACE_RUNTIME_LIMIT_CONTRACT`.** No observation, Save
or Confirm click, submission, or model call occurred. The runner emitted
`RUNNER_RESULT.json` with `runner_exit=1`, `ValueError('max_runtime_ms must be
one to 10000')`, and an empty fixture oracle. An independently invoked,
network-disabled pinned-container raw auditor returned `FAIL_RAW_AUDIT`, 10/29
checks, with the expected missing-task fields and explicit identity/result
failures; it did not misclassify this setup STOP as a task result.

The runner and audit output are retained. Formal-03 is not retried. A successor
must set the bounded method runtime to at most 10,000 ms and statically validate
the exact interface before starting Chromium.
