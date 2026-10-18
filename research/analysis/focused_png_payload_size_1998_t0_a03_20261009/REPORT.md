# Issue #1998 A03 — formal HOLD

**Disposition: `HOLD_RUNNER_EXIT_UNCAPTURED`; scientific result not evaluated.** The frozen candidate was invoked once under macOS `sandbox-exec` network denial. It emitted 561,847 bytes of JSON that parses structurally as 23 rows for the frozen allocation. Candidate stderr is empty. The exact raw output SHA-256 is `e7d7f1012006fc105c3aa83c6c7311eb41d240bdedfa9acc1bd13d0337b1f3ac`.

The wrapper then failed with `zsh:1: read-only variable: status` while trying to record the candidate process exit code. The candidate's exact exit status and finish timestamp were not captured. Parseability and empty stderr are not substituted for that missing exit receipt. Under the frozen rule, the independent auditor is invoked only after a confirmed candidate exit 0, so auditor invocation count is 0. The allocation is consumed, retries are 0, and no candidate rerun or auditor invocation is claimed.

The output therefore supports no conclusion about PNG crop reconstruction, serialized-byte savings, fallback behavior, or mutation adequacy. It is retained as unaudited raw candidate data only. OrbStack image inventory had stopped before listing images on a containerd content-blob `operation not supported` error; no container was started. This execution used CPython 3.14.5 on macOS arm64 under network denial and is not container evidence.

The construction suite passed 6/6 in normal and optimized modes before freeze. That construction result does not repair the formal run-custody gap. All source and raw hashes, the freeze, and exact protocol remain additive in this package.
