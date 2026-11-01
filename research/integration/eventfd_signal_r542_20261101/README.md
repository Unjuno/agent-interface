# One-shot eventfd probe r542

In one fixed-order, three-arm local Linux run using Python 3.11.2 and `spawn`,
the unrevoked child observed no readability, the child released after the
parent's one write observed readability, and a parent write returned after the
attached child was killed and joined (exit -9). The saved JSON includes the
individual syscall timing observations; each is one sample and is not a hard
latency bound or comparison to model or GUI time. Fixture children were joined.

The conditions and script were fixed before running. The parent kept the
eventfd open and the child did not read or drain it. Passing an fd using DupFd,
one successful poll and one successful write do not establish a complete
ownership or recovery protocol. In particular, an action already past a check
can still run after the write; descriptor loss, process crashes at other points,
saturation/EAGAIN, stop-and-resume, X-server queued input and other platforms
remain untested. This is not an MCP integration, release confirmation, task
success or a WSLc/MAP01 result. Compare the lock-owner-death counterexample in
the adjacent `event_lock_r540_r541_20261101` evidence.

The script records outcomes rather than asserting the preregistered arm
expectations; the comparison above is an external reading of the JSON. Review
also identified that a process-start exception can cause joining an unstarted
process to skip subsequent descriptor cleanup. No such exception occurred in
this run, but the harness needs stronger construction-failure cleanup before
reuse outside a short-lived container.

The output is an unchanged copy of the controller capture. Docker image and
flags are recorded in CONDITIONS.md but are not independently attested by the
JSON. No physical input or user GUI was used.
