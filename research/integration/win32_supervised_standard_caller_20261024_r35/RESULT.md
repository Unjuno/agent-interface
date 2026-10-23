# R35 — sub-second recovery-state diagnostic

**Classification: diagnostic evidence only; strict R29 gate FAIL_OR_UNKNOWN.** One fresh fixture, one public dispatch, and one recovery sequence were run on the user-authorized Windows PC. No replay or second attempt occurred. The raw trial is `raw.json`; the pre-run custody record pins the conditions and source files.

A separate process independently read the fixture's exact generation as `Q=true` before cancellation. The recovery `VK_Q` key-up `SendInput` returned after 311.077 ms. After that return and before the held Q-up hook callback returned, the same-generation sampler recorded 105 `Q=false` samples (sample interval about 10 ms). This is positive evidence that the target state became neutral during the blocked callback window in this diagnostic.

The callback lasted 1,490.357 ms although the planned hold was 700 ms. R35 recorded only four public status polls during the hold, below the frozen R29 requirement of 21. Therefore the strict R29 gate is not satisfied, even though the observed callback duration exceeded 1,250 ms. The hook trace shows no second distinct Q-up callback. The independent sampler ended `unknown` with `unknown or stale target fixture` after teardown, so the complete series did not exit cleanly. Overall probe status is `FAIL_OR_UNKNOWN` with a TaskGroup exception.

The fixture click/save oracle matched at save time (`clicked=true`, `saved=true`, empty text) before cancellation. A later `q` character event was recorded after the save. Runtime `task_success` remains null; no post-cancel task-success claim is supported. Foreground restoration and fixture exit were observed.

The frozen R35 audit was executed once and stopped with `NameError: readback is not defined`; its execution record is preserved in `audit_frozen_execution.json`. The copied supplemental R34-shaped evaluator produces `FAIL_OR_UNKNOWN` because its expected fields (such as public cancel, result readbacks, and public close attempts) are absent from R35's raw schema. `evidence_review.json` is the explicit R35 field-to-evidence review; it does not modify the frozen evaluator or alter the strict gate.

This result narrows the uncertainty: an independent state read can observe Q-up before the held callback returns, but hook delivery, complete status-poll coverage, clean sampler teardown, and post-cancel task success remain unproven. This is not MAP01, WSLc, broad reliability, or efficiency evidence.
