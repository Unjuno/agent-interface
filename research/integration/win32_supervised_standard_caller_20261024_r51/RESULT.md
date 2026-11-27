# R51 result

Disposition: `PASS_SCOPED` for one paired native-Windows supervised-caller fixture sequence. The input-free preflight passed 14/14, phase 1 passed the frozen strict release audit 11/11, and the combined audit passed 13/13. R51 is a new attempt, not a replay of R50.

Phase 1 used one public dispatch and one public cancel. Cancel response took 1.9516 ms. The same-generation Q-up callback remained held 1,400.3203 ms after the cancel response; 89 exact-call polls covered the hold. Recovery Q-up `SendInput` returned after 310.6963 ms. The independent sampler recorded 74 eligible same-generation Q-up samples and exited normally with 598 samples. The complete strict release audit passed.

Only after the strict gate passed, phase 2 used a new fixture process/window, target generation, call, operation, task token, and oracle ID. The public action completed with `release_confirmed=true`, neutral key/button state, and independent state-query witnesses. The external task oracle verified the exact frozen click/save/token effect and returned a success receipt bound to the new call ID, operation ID, target generation, and oracle ID. The initial dispatch response leaves its action-level `task_success` null; the subsequent standard `interface_verify_task` response is `status=verified, task_success=true` ([raw response](run/phase2_task/verify-task-0.json)). Thus the scoped attempt did obtain an integrated task-success result after the independent verification call.

The fixture effect-file write-return to independent oracle read-start interval was 256.4395 ms. This is a fixture/file observation interval, not physical input-to-effect or durable-storage latency. The later session-close record reports `release_confirmed=false`; the completed action's retained release receipt and independent neutral readback are the passing evidence for this phase.

Both phase processes exited 0, the public session closed with no unresolved calls, and foreground restoration passed. The attempt used Python 3.13.14 on current main `47d5e9b6c45ecabd682f71731244dbc085ffa88f`. It used the user-authorized Windows PC, with no WSLc or Docker operation.

R51 repairs the R50 harness configuration issue: R50 supplied a 36-character dashed UUID as `oracle_id`, which the public verification API rejected before it could accept a bound task receipt. R50 remains `FAIL_OR_UNKNOWN`; its raw files and original audit were not altered. R51 adds a preflight guard and confirms the corrected path once. This does not make a broad reliability estimate. It remains fixture evidence only; real-app/MAP01 transfer, matched efficiency, model/token accounting and broader reliability are open.

The private raw packet is preserved with a SHA-256 manifest. The public derivative redacts workstation paths, host name and the previous foreground window title; public manifest verification confirms the sanitized packet.
