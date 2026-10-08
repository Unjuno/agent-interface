# Primary stdio busy-bound evidence rescue

This rescue preserves the additive evidence from PR #6902 without merging its
runtime or workflow modifications. The two retained evidence packages are:

- [`../primary_stdio_busy_bound_57_20261003_01a0ff59/README.md`](../primary_stdio_busy_bound_57_20261003_01a0ff59/README.md)
- [`../primary_stdio_busy_ci_57_20261003_01a0ff59/README.md`](../primary_stdio_busy_ci_57_20261003_01a0ff59/README.md)

The package reports `PASS_PRIMARY_BUSY_BOUND_SCOPED` for a finite Windows/Node
stream regression: the candidate retains at most one unobserved `busy` write,
preserves the committed command/result, and exits conservatively on overload.
The retained evidence does not establish a global byte bound, permanent-stall
deadline, downstream consumption, physical release, task effect, performance
gain, or hosted Ubuntu/Python equivalence. No formal allocation or shared
resource was used.

The read-only v2 auditor was rerun against the rescued `pipe/` directory and
returned `PASS_PRIMARY_OVERLOAD_OWNER_SCOPED`: baseline 2 busy responses and
candidate 1, one committed command per arm, one relay request per arm, and
relay exit 0 in both arms. This confirms the retained packet; it does not
expand its scope.

The production source change and `.github/workflows/native-mcp-v1.yml` change
remain only in PR #6902's source branch. They are intentionally not included
in this rescue because the PR is based on an older main and has not supplied a
current-main CI result. This file is the integration disposition; the copied
evidence packages remain byte-preserved under their own manifests.
