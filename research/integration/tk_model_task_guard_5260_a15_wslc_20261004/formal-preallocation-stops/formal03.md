# formal03 STOP — candidate output existed before dispatch

Allocation: `5260-a15-model-paired-formal03-20261004`

The trusted exchange host initialized successfully. The candidate WSLc command
started, verified its frozen source closure, then stopped at the runner's first
output creation because `/out/candidate` already existed. This directory had
been pre-created as an “empty output” check; the runner intentionally requires
the output path not to exist (`exist_ok=False`).

No owned GUI or exchange request was started, and no provider call occurred.
The WSLc launch output and host-owned records are preserved. This allocation is
not retried. A new allocation will keep the candidate output path absent and
will preflight absence (not emptiness) before dispatch.
