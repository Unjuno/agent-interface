# R30 result — process retirement did not span the blocked-hook interval

**Strict outcome: FAIL_OR_UNKNOWN (19/20).** A fresh current-main supervised Win32 fixture returned `pending` on one cancellation. The 1,253.867 ms post-cancel hook hold ended while the callback was still inside its bounded wait; 20 read-only same-call polls all stayed `running / pending / release_confirmed=false`. The audit's sole failure is still release and independent Q-up while the native callback remains blocked.

R30's trace-only wrapper captured the exact producer PID `51176` inside `OperationCancellationSupervisor._retire_process`. That method entered 1.389 ms after cancel start. `terminate()` returned in 0.106 ms; `join(0.1)` returned in 4.128 ms; the following `is_alive()` returned false. `_retire_process` returned true 7.184 ms after it entered, about 8.573 ms after cancel start and well before the callback ended.

The callback returned 0.284 ms after the planned hold ended. Only afterward did the public transaction reach recovered/release-confirmed; the independent same-generation neutral readback, exact fixture effect, producer cleanup, session close, and foreground restore passed. The user-current registry value remained absent. The separate Q-up observation while the original Q-down was still intercepted is not release evidence. Runtime `task_success` remains null.

This rules out slow `terminate()`/`join()` as the observed 1.25 s stall in this sample. The next remaining boundary is the recovery helper's `_recover` → `Win32Backend.release_all()` → `SendInput` path, which R30 did not instrument. A blocked recovery call is a leading hypothesis, not yet proven. The result is one local Windows fixture sample; it does not establish kernel causality, WSLc, MAP01, efficiency, or broad reliability.

Input-free preparation retained three instrumentation setup stops and a final PASS. The fake-process preflight exercised every wrapper method without native input, and the preflight receipt records the `conditions.json` hash. The trace adds small file-write overhead around retirement calls; no runtime source changed.
