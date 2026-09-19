# Live delayed evaluation through the shared outcome wait policy

The preceding replay test left live continuation unverified. This probe runs
frozen socket v10 / interactive v26 in private Linux/X11 xterm fixtures and sends
real keyboard input. A test-only wrapper gates entry to the ordinary independent
evaluator. It changes neither input admission nor evaluation logic. The controller
waits for the input terminal and the evaluator's waiting marker before issuing
the common outcome request with a 100 ms timeout.

Both cases return pending with task_success unset while the gate is closed.
The probe then releases the gate and uses exactly the returned read-only
continuation. The correct token yields true; a wrong token yields false after
the existing evaluator's roughly three-second mismatch polling interval.

| Case | Pending socket call | Gate duration | Terminal to evaluation known | Final result |
|---|---:|---:|---:|---|
| Correct token | 101.188 ms | 111.976 ms | 125.214 ms | true |
| Wrong token | 101.122 ms | 112.186 ms | 3132.564 ms | false |

Each case has exactly one submit command, one accepted program, a completed
terminal with verified input release, and three exact AIT/PNG frames. The saved
token matches what was typed; only the correct one passes the independent task
oracle. Accepted/terminal/evaluation request lineage agrees. Collected responses
cover the complete delivered prefix, including non-outcome records. No runtime
rejection occurred. Both processes exited zero and removed their socket paths.

The test demonstrates continuation after an observed live evaluation delay
without input resend, and distinguishes an evaluated failure from a timeout.
It does not test evaluator exceptions, lost publications, process restarts,
permanently stalled scoring, or delayed browser HTTP responses. The gate has a
ten-second test watchdog and is deliberately held only until a pending response
is received. No claim about naturally occurring delay frequency follows.

This is a scripted fixture probe (decision evidence explicitly says scripted),
not actual assistant self-use or a human-speed comparison. The small timing
samples measure this injected wait and transport, not model thinking or tokens.
The generic helper remains a candidate. A finalizer exception can still leave
no final outcome event, requiring status inspection; handling that path is the
next completion-contract gap.

Evidence: results/live-outcome-wait-01. Each case preserves socket requests and
responses, evaluator gate timestamps, raw runtime records, saved output, image
artifacts and stderr. probe_live_outcome_wait.py verifies runtime source hashes,
frame fidelity, result, prefix coverage and no duplicate submit. Root sources.json
also hashes the test wrappers, helper and transport sources. Frozen code was not
edited to install the test gate.
