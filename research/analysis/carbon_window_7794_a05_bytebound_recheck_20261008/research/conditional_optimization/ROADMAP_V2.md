# Conditional optimization lane: evidence-driven roadmap v2

BASE: `120a1b8de6d515d75c2200ca3acc310a124fb373`.
This additive lane plan does not replace the active coordinator, top-level
roadmap, existing formal leases or historical failure dispositions.

## Current disposition

The previous conversation's v1 archive was checked: 20 manifest entries matched,
eight tests and eleven aggregate checks passed. Its encoder is imported
byte-exact as a control. The entire old raw archive is not claimed to be in
this directory; it remains in the conversation attachment.

The new opt-in v2 removes a duplicated repeat-frame comparison. It composes with
the unchanged upstream AIT1 Decoder and actual ImageArtifactSink. Twelve
integration tests cover byte identity, PNG publication/reuse, current context,
geometry/mode changes, serialization rollback, dropped/reordered packets,
reconnect and refusing to overwrite existing artifacts.

The first performance allocation completed, but its raw records disappeared
before durable upload. Final disposition is FAIL_EVIDENCE_RETENTION, not a
promotable performance PASS. Do not recreate or rerun that allocation ID.
See `transport-integration-v2/RETENTION_FAILURE.md`. A separately identified
construction recheck passed 12/12 and its complete stdout and source hashes
are durable in `construction-validation.json`; it does not rescue the lost
performance record.

## Ordered next tasks

1. **Close the measured retention blocker.** Before a new performance allocation,
   retain all source and input identities remotely, checkpoint complete raw
   results and require read-back hash verification before any promotion claim.
   A SHA without retrievable bytes is insufficient. Use a new ID; preserve the
   first retention failure even after a later successful trial. This is a
   concrete reproducibility blocker, not packaging or cosmetic cleanup.
2. **Evaluate conditional routing, not universal replacement.** Keep O1, O2,
   v1 and v2 controls. Preserve the sparse-header counterexample and dense
   conditions that favor O1. Changed tile count does not determine compressed
   packet size. Include route-selection and PNG-publication cost; do not tune
   only the retained seed or equate wire bytes with model tokens.
3. **Real desktop caller integration.** Choose one existing independently
   scored workflow and account for cold acquisition, warm reuse, invalidation,
   bounded repair and subsequent reuse. Charge all attempted model calls,
   images, local observations and full task time. Runtime safety and independent
   task effect are hard gates; this codec composition is not whole-GUI proof.
4. **Revisit rejected memory under a changed condition.** Preserve the rejected
   OpenTTD crop result. First establish a task where current-only evidence is
   insufficient; then compare a new occlusion-cleared or landmark-preserving
   crop with full history and current-only, holding model and scorer fixed.
5. **Integrate only justified compatible mechanisms.** A compact dictionary or
   native rewrite requires a measured model-boundary/reuse or local-CPU
   bottleneck. Keep evidence, target identity, input authority and independent
   effect separate. No speculative component sweep is authorized by this note.

DOOM remains in the separately coordinated dynamic-control lane. Desktop tasks
measure repeated-work economics; synthetic/replay tasks isolate costs cheaply.
Compiler specialization, feedback control and distributed state management
supply useful design connections, not evidence of correctness by analogy.

## Parallel execution

This task writes only new files under `research/conditional_optimization/`.
Shared runtime, workflows, existing result trees, source freezes and the active
MAP01 recovery runner are unchanged. A successor declares TASK/BASE/branch and
exact paths in Issue #60. It must not adopt a moving main silently, reuse a
consumed allocation ID, infer that an unreported worker has stopped, or launch
an external Worker without an actual session. Code/result publication via PR
is distinct from enabling a default runtime route.
