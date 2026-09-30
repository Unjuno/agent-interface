# Issue #5044 formal result — FAIL

## Question and frozen decision rule

This is the successor experiment for the disclosed #5021 ARM64 timing-boundary
confound. It reruns the exact predecessor candidate schedule with `heapq`
imported at module load, before each queue timer. The primary outcome is paired
`process_time_ns` for queue construction plus full drain (15 blocks per size).
The preregistered hypothesis passes only if the median heap/list CPU ratio is
at most 0.80 against **both** `STABLE_LIST_SCAN` and `STABLE_SORTED_LIST` at
both sizes 512 and 2048. All 225 one-shot workers are required.

## Result

**FAIL — `FAIL_HEAP_COST_THRESHOLD_NOT_MET`.** The timing-boundary correction
removes the import confound, but the preregistered crossover hypothesis fails:

| Candidate count | Heap / scan median CPU ratio | Heap / sorted-list median CPU ratio | 0.80 rule |
| ---: | ---: | ---: | --- |
| 512 | 0.052138 | 1.029133 | Fail: sorted-list comparison exceeds threshold |
| 2048 | 0.014979 | 0.768888 | Pass |

Ratios are medians of 15 same-block paired comparisons. Thus the heap is much
faster than the deliberately quadratic scan at these sizes, and clears the
sorted-list threshold at 2048, but does **not** clear it at 512. The frozen
conjunctive hypothesis is rejected; this experiment does not support adopting
the heap on the claimed two-size/two-baseline criterion. It does not establish
production scheduler benefit or generalize beyond this synthetic schedule and
the pinned CPython 3.12.14 Linux/aarch64 environment.

## Evidence and audit

- OrbStack Docker, pinned image ID
  `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`,
  linux/arm64; network disabled; read-only root and source/input; 0.25 CPU,
  512 MiB memory, 64 PIDs, all capabilities dropped, no-new-privileges.
- Exactly one formal container invocation; exit 0; 225 fresh worker processes;
  zero retries. Runtime reported CPython 3.12.14, `aarch64`, Linux 7.0.14
  OrbStack.
- Raw packet: 2,928,716 bytes, SHA-256
  `a9999afb3c44a5b358ddd8b15714bc5afde4fdb1565226a31be253044e9d17cf`.
- A distinct network-disabled container independently audited the raw packet
  against the frozen source and schedule. It reconciled all 225 rows and all
  225 traces; errors were empty; 13/13 corruption controls were rejected.
- Audit decision and ratios are in `../audit01/audit.json`; exact invocation
  receipts are alongside the raw and audit outputs.

## Local checks and limits

- Allocation unit tests: 5/5 passed on the host Python 3.14.5; construction
  tests had also passed 5/5 inside the pinned Python 3.12.14 container before
  formal freeze.
- `git diff --check`: passed.
- A broad host run of `python3 -m unittest discover -s runtime -p 'test_*.py'`
  collected 269 tests and ended with 6 skipped, 12 failures, and 8 errors.
  These were outside this allocation; observed causes include missing `mcp`,
  `Xlib`, and schema-validator dependencies, producing validator-unavailable
  expectations. This is not a green repository-wide CI result.
- The workspace index checker is not a valid check in this sparse checkout:
  the checkout includes only selected research subtrees while its index names
  many absent directories. No repository-wide CI workflow files are present
  in this worktree's sparse view. The target's focused tests and actual
  preregistered experiment/audit are the validated gates here.

No follow-up tuning or replacement run was performed. Any changed threshold,
schedule, or worker source requires a new successor allocation; this failed
result and raw evidence remain immutable.
