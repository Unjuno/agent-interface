# One-shot WSLc protocol — T0c

## Runtime

- Use Microsoft WSLc (`wslc.exe`) only for this local CPU/single-container study; no Docker/Podman substitution.
- Cached immutable image `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64, Python 3.12.14).
- Per run: `--pull never --network none --cpus 1 --memory 1G --user 65534:65534`.
- Mount source read-only. Candidate writes to a fresh output mount. Auditor gets only its own read-only source plus frozen raw candidate JSON and a fresh report mount; it does not import candidate code.
- Before start, inspect `wslc ps --all --no-trunc` and host processes for an active WSLc owner operation. Do not inspect/stop/remove another owner's containers; if any live owner exists, wait or record STOP.
- Preserve the exact swap/cgroup warning. Check `/sys/fs/cgroup/memory.max` from inside construction: it must equal `1073741824`. Swap limit is unavailable and is an explicit resource limitation; do not claim swap isolation.
- Keep every created container, including exited/failed ones. No `--rm`.

## Freeze and gates

1. Confirm branch is based on the current GitHub main SHA. Recheck Issue #6477, related #6461/#6179, branches, open/closed PRs, local active worktrees, and owner/resource status. Confirm there is no overlapping allocation.
2. Run final host test/mutation suite. Freeze exact source SHA-256, issue allocation ID, main SHA, image ID/digest, runtime version, and UTC time in `FREEZE.json`. Do not edit frozen candidate/auditor after this point.
3. Immediately before WSLc construction, recheck GitHub main and active owner state; if main changed since freeze, write STOP and stop. Run construction suite once. Require exit 0 and `memory.max=1073741824`.
4. Before candidate, repeat main/owner/hash checks. Run candidate exactly once to fresh raw JSON. Nonzero exit => preserve raw/output and record `FORMAL_FAILURE.md`; never retry.
5. Before audit, repeat main/owner/hash checks. Run independent auditor exactly once with raw only. Nonzero exit or non-pass => preserve all evidence and record `FORMAL_FAILURE.md`; never rerun candidate.
6. Write report with exact commands, UTC start/end, exits, complete warning/stdout/stderr, container IDs, raw/audit SHA-256, row counts, results and scope. Do not promote synthetic results beyond preregistered limits.

## Stop conditions

STOP before the next rung if main advances after freeze, a WSLc owner conflict appears, memory.max is not exactly 1073741824, source/image identity is uncertain, mounts are not fresh/read-only as specified, or the previous rung exits nonzero. A STOP is not scientific FAIL. T0b remains a separate terminal allocation.
