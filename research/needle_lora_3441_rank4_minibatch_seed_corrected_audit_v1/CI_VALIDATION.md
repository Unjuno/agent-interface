# PR #3922 CI failure — local Docker reproduction and correction

The initial head `97b54b399bf8414f0c0bf2971bba8038f60565f4` failed
`Research Workspace Index` job 106161661550 at step
`Check top-level research directories are indexed`. The failure was caused by
the new top-level audit directory not being linked from the exhaustive
`research/ROOT_NAMESPACE_MAP.md`.

## Local reproduction

The failed workflow command was run from a read-only local Docker Desktop
container using cached `python:3.12-slim`, `--network none`, CPU 1, 512 MiB
memory, a 16 MiB noexec tmpfs, and the checkout mounted read-only. First, the
local checkout also exposed an ignored `research/__pycache__` created by an
earlier unittest module import; that exact generated cache was removed, and
`PYTHONDONTWRITEBYTECODE=1` prevented recurrence. The clean reproduction then
reported only the unindexed audit directory, matching the CI failure.

Added one direct-root entry for this audit in `research/ROOT_NAMESPACE_MAP.md`;
the issue's original HOLD and predecessor artifacts were not changed. The same
container command then passed: `research workspace index OK: 124 top-level
directories reachable` (exit 0). This is an index-integrity fix, not a
row-level audit or scientific result. The separate `map01-3270-replay-gate`
workflow was still in progress at this validation snapshot and is not claimed
here.
