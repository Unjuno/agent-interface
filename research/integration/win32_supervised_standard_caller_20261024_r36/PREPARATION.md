# R36 preparation

R36 is a one-shot strict cancellation trial on the user-authorized local Windows PC. It addresses R35’s source-level `hold_ms` UnboundLocalError, records the public cancel attempt before invoking it, gives the held callback a 3000 ms absolute self-deadline, budgets the 1 s cancel timeout plus the full 1250 ms hold, requires at least 21 same-call status polls, and stops the independent same-generation sampler before closing its fixture.

Preflight is input-free. The live trial requires an exact-generation Q-down baseline, one dispatch, then at most one public `interface_cancel`. Any mismatch aborts before cancel; any post-cancel error releases the hook in `finally`. No replay, retry, WSLc or Docker. Runtime `task_success` remains null unless the runtime itself supplies independent evidence.
