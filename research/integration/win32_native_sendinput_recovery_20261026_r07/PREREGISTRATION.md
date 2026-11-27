# Win32 R07 — bounded recovery followed by a fresh-generation task

## Frozen sequence

R07 is one trial on the authorized Windows workstation. It first repeats R06's held-SHIFT boundary using an owned fixture and the standard supervised public MCP tools. The first phase must verify real SHIFT-down while the producer is blocked at its injected SHIFT-up `SendInput` callable, one cancel, terminal recovery within the 3,000 ms cleanup deadline, and independent same-generation SHIFT-up readback. If any first-phase gate fails, no continuation action is attempted.

Only after that pass, R07 closes the first server, retires its exact fixture process, starts a fresh fixture and supervised session, and requires both PID and target generation to change. It submits a focus-only public dispatch with the retired generation and requires `TARGET_GENERATION_CHANGED` plus `input_dispatched=false`. It then observes the fresh generation and runs one `run_public_compiled` transition through public `interface_observe` and `interface_dispatch`: click the frozen fixture point (100,60), type `office`, Ctrl+S, and release all input.

The caller-side postcondition must read the exact effect only after a fresh public observation whose capture begins after dispatch response return. The separate server-configured `interface_verify_task` oracle must verify `{saved:true,text:"office",clicked:true}` and bind its receipt to the exact action call ID, operation ID and fresh target generation. A native post-action state readback must report SHIFT, CTRL, S and left mouse button up on that generation.

## Frozen pass rule

Classify `PASS_RECOVERY_FRESH_GENERATION_TASK` only if phase 1 meets the R06 gates, the old fixture exits before phase 2, fresh PID and generation differ, stale-generation input is refused, exactly one compiled task action is dispatched, the action release and native neutral-state readback pass, the post-observation timing is fresh, the fixture journal contains exactly one click, the six `office` character events in order, and one save with the exact effect, and the independent oracle verifies the exact call/operation/generation. Otherwise preserve the first `FAIL_OR_UNKNOWN_FIRST_OUTCOME_RETAINED` result and do not retry this attempt.

## Limits and evidence

The SendInput fault is injected before the native Windows function; recovery and state readback are native. This does not prove an OS/kernel-level API hang or arbitrary I/O guarantee. The task uses a fixed safe point and no model; it does not measure AppServer/provider efficiency, WSLc, MAP01, broad reliability, or production-app correctness. No WSLc or Docker allocation is used. Raw reports, fixture logs, timing, identities, and cleanup outcomes are hashed after cleanup. Local paths remain local.
