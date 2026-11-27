# Issue #8592 A01 source archive

Exact package copied from branch `research/8592-dpor-t0-a01-20261008` at
`b0951ae1a8cfd5befbb6988935dd4d931f595fb2`.

The Issue records one WSLc candidate invocation that exited 1 before candidate
code loaded because the individual-file bind mount exposed `/run_candidate.py`
as a directory. Candidate output and auditor invocation were both absent. This
is A01's execution-integrity failure, not a method result. The frozen allocation
was not retried or reclassified. The later A03 result is a separate allocation
retained in merged PR #8602 and does not alter A01.

No candidate, auditor, model, or GUI was run while archiving these files.
