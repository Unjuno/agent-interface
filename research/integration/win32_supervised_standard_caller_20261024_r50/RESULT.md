# R50 result

Disposition: `FAIL_OR_UNKNOWN` for one paired native-Windows supervised-caller attempt. The input-free preflight passed 13/13. Phase 1 passed the frozen strict release audit 11/11, and phase 2 began only after that gate. The overall frozen audit passed 8/13. No retry or replay occurred.

Phase 1 used one dispatch and one cancel. The callback remained held 1,400.7461 ms after cancel response, with 89 same-call polls and 74 eligible same-generation Q-up observations. Recovery Q-up `SendInput` returned after 310.1411 ms. The sampler exited normally with 598 samples. These satisfy the frozen release gate for this one sample.

Phase 2 used a new fixture process/window and target generation. The action report records completion, `release_confirmed=true`, neutral key/button state and state-query witnesses. The exact fixture effect file matched the frozen click/save/token values. The bounded public task verification did not produce a valid receipt: `interface_verify_task` returned `unknown`, with `independent_task_oracle_receipt_invalid: ValueError('oracle_id must be 32 lowercase hexadecimal characters')`. R50 had frozen a dashed UUID as its oracle ID. The phase-2 harness then exited with an `ExceptionGroup`; its top-level task result lacks accepted generation/call/operation fields, so the combined audit correctly fails the bound-oracle, phase-2 gate and cleanup checks. Runtime `task_success` remains null. This is a R50 harness configuration defect, not evidence that the public task-verification path succeeds.

The exact fixture write-return to the attempted oracle read-start interval was 253.1832 ms. Because the oracle ID was rejected and no task receipt was accepted, this is a local effect-file interval only; it does not qualify end-to-end task completion latency. The fixture and caller processes exited, the foreground was restored, and no input remained in the owned fixture.

The experiment used Python 3.13.14 on current main `47d5e9b6c45ecabd682f71731244dbc085ffa88f`. It was conducted on the user-authorized native Windows PC. WSLc and Docker were not used. R50 does not establish task success, MAP01 or real-app transfer, matched efficiency, broad reliability, or WSLc behavior.

The original raw, condition, audit and process receipts are preserved. `R50_POSTRUN_DIAGNOSIS.json` records the frozen configuration error. The private original packet has its own hash manifest; public receipts redact local paths and the host identity without changing the observed trial outcome.
