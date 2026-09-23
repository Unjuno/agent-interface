# Interruption-safe semantic checkpoint contract (#2661)

Pure contract-only successor. It validates session/task binding, monotonic
epoch, explicit effect status, evidence reference, invalidation, and a fresh
authority requirement. A confirmed checkpoint is only `ADMITTED_FOR_REVIEW`;
the validator never grants authority or asserts task completion. Provisional
and unknown effects yield, and stale/contradicted/session/task invalidation
refuses.

Run the finite unit matrix in the pinned Docker Python container. No GUI,
model, provider, input, task oracle, latency, token, or recovery-rate claim is
made.
