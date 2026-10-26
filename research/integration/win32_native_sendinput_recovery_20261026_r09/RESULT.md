# R09 result — bounded recovery, generation fence, and fresh compiled task

**Scoped result: `PASS_RECOVERY_FRESH_GENERATION_TASK`; independent audit: 14/14 checks, 38/38 raw hashes, 3/3 pretrial hashes.** R09 joined bounded recovery to a fresh-generation task in one retained run.

In phase 1, a real SHIFT-down was observed while the producer-local SHIFT-up `SendInput` callable was held. One public cancellation returned `pending`; retained terminal custody later reported `recovered` and `release_confirmed=true`. Owner recovery completed in 16.869 ms under the configured 3 s cleanup deadline, leaving 2.983 s of margin. A separate same-generation native state query confirmed SHIFT-up. No emergency release was used, and the old fixture exited cleanly.

Phase 2 started a different fixture PID and a different native target generation. A public focus-only dispatch bound to the old generation returned `TARGET_GENERATION_CHANGED` with `input_dispatched=false`; no stale effect occurred. Then `run_public_compiled` used two public observations and exactly one public action on the fresh generation. The action-level receipt confirmed release, and independent native readback found SHIFT, CTRL, S and left button up.

The fixture recorded exactly one click, the six `office` character events in order, and one save. The independent effect file matched `{saved:true,text:"office",clicked:true}`. A post-dispatch observation began 3.582 ms after the action response returned. The server-configured `interface_verify_task` oracle returned `verified/task_success=true`, bound to the exact action call ID, operation ID, and fresh target generation. The fixture exited with code 0 and the previous foreground window was restored.

R07 and R08 remain separate immutable failures; R09 fixes their probe schema, cleanup-path, oracle-ID, and audit-field mistakes without editing them. Their assessments are [R07](../win32_native_sendinput_recovery_20261026_r07/ASSESSMENT.md) and [R08](../win32_native_sendinput_recovery_20261026_r08/ASSESSMENT.md).

## Scope limit

The blocked producer was held at an injected Python callable before native `SendInput`; the actual cancellation recovery, task inputs, release and readbacks were native Windows behavior. This does not demonstrate a Windows/kernel hang inside `SendInput`, an arbitrary I/O guarantee, AppServer/model integration, WSLc, MAP01, matched efficiency, production-app correctness, or a reliability rate. No WSLc or Docker allocation was used. This experiment used a fixed fixture point, not a model-selected coordinate.
