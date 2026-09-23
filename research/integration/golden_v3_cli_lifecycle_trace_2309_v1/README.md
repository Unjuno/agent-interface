# Golden v3 → CLI lifecycle trace #2309

Status: PASS_GOLDEN_V3_CLI_LIFECYCLE_TRACE_SCOPED

This additive fixture executes a deterministic ten-state lifecycle trace through a small model/vendor-neutral adapter boundary. It retains setup, model attempt, observation, guarded dispatch, refusal, useful effect, stale invalidation, repair, terminal release, and cleanup failure. The adapter never grants authority by translation; task success is separate from program completion, and cleanup failure is non-success while preserving the execution result.

Native and Python 3.12-slim container audits must emit the same canonical result digest. This is a runtime-trace contract test, not live GUI, model, network, input, latency, or end-to-end task evidence.
