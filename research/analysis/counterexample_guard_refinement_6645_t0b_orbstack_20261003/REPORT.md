# Issue #6645 — A02 retained preformal STOP

A02's pinned OrbStack construction suite passed 13/13. The subsequent formal
container launch failed before container creation because the command's image
digest was inadvertently truncated. Candidate and auditor formal invocation
counts are 0/0; no H-pass/fail inference is possible. Preserve this operator
STOP without retrying A02. See
[`results/preformal_01/STOP.json`](results/preformal_01/STOP.json). A01's
independent construction/environment STOP remains preserved in the adjacent
`t0` package.
