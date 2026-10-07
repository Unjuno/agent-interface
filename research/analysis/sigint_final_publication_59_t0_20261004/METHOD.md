# H/T/D/C/U — F03 final-summary SIGINT window probe

Hypothesis: unmasking a pending SIGINT after writing a passing terminal summary can raise KeyboardInterrupt only after the persisted file contains PASS.

Treatment: a standalone, freshly written Python 3.12 script starts a child process. The child blocks SIGINT, writes a PASS JSON summary, queues SIGINT to itself, then restores the old signal mask without catching KeyboardInterrupt. The parent records the actual child return code and reads the persisted file. The probe does not import, execute, or modify F03 source, tests, producer, or auditor.

Data: one deterministic synthetic POSIX signal-control run in WSLc using the pre-cached `python:3.12-slim` image; network disabled, 0.5 CPU and 128 MiB configured, tmpfs `/tmp`. Outcome has no stochastic component.

Comparison: the safe expected outcome would preserve STOP/non-PASS after interruption; this treatment tests the vulnerable publication order in isolation.

Uncertainty: this validates Python/Linux signal delivery and publication ordering only. It does not execute or empirically qualify F03, filesystem crash durability, SIGKILL, storage failure, timing under load, or formal experiment custody.

The preliminary inline attempt's displayed `130` was a simulated value, not the child process status; its output is retained but superseded. The output audit is a separate program by the same worker, not an independent review. The initial committed-tree audit also found Git's line-ending normalization could invalidate exact-byte evidence; package attributes and optional commit-tree verification now cover that boundary.
