# Run protocol — allocation 6179-T0B

## Runtime and isolation

- Runtime: Microsoft WSLc (`wslc.exe`), from WSL/Windows host; do not substitute Docker or Podman.
- Image: cached immutable `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f` (linux/amd64, Python 3.12.14).
- Per invocation: `--pull never --network none --cpus 1 --memory 1G --user 65534:65534`.
- Mount source read-only and each output directory writable but otherwise fresh. Candidate consumes only frozen source. Auditor receives only frozen auditor source and candidate raw JSON; it must not import candidate.
- No GPU, model, GUI, live verifier, production credentials, user data, network access, or external effects.
- A WSLc container from a prior allocation printed `wsl: Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.` This is retained prior-runtime evidence, not yet observed in this allocation. If emitted again, preserve it verbatim and stop before candidate unless the 1 GiB memory limit is confirmed enforced; without swap quota, configured memory may be incompletely constrained.
- Do not inspect, stop, remove, or otherwise alter containers owned by another task. Retain every container created here, including exited and failed containers.

## One-shot gates

1. Before freeze, sync the research branch to the then-current `origin/main`; re-read Issue #6461, search GitHub branches/PRs for collisions, check working tree and exact source hashes. Freeze only after final construction tests pass. Record exact main SHA, branch, source SHA-256 values, image digest, invocation count limits, and UTC time in `FREEZE.json`.
2. At formal start, verify the freeze hashes; inspect current WSLc container inventory and host processes for an active runtime owner/conflict; verify the current-main base has not advanced. If any gate is unavailable or conflicting, write `STOP_BEFORE_FORMAL.md`, record candidate/auditor invocations as zero, and do not start a container. Because prior WSLc output reports missing swap-limit/cgroup support, confirm the 1 GiB memory ceiling is enforced or STOP before candidate.
3. Run the construction suite once in WSLc. Nonzero exit => retain output, write `FORMAL_FAILURE.md`, and stop. No retries.
4. Only after gate 3 passes, run `candidate.py` once to a fresh raw JSON output. Nonzero exit => preserve raw/exit/output, write `FORMAL_FAILURE.md`, and stop.
5. Only after gate 4 passes, run `auditor.py` once against raw JSON into a separate fresh report directory. Nonzero exit or any non-pass report => preserve all evidence and write `FORMAL_FAILURE.md`. No retries or candidate edits after freeze.
6. On completed audit, write `REPORT.md` with exact command lines, runtime banner/warnings, UTC start/end, exit codes, raw/audit hashes, row counts, outcomes, and explicit limitations. Preserve stdout/stderr and raw/report bytes. Never overwrite a consumed allocation; any correction requires a new successor allocation.

## Expected container shape

Illustrative only; establish and record exact Windows path mapping for WSLc before the one-shot run. Use `wslc run` in the syntax supported by the installed 3.0.1.0 runtime, pinned image, no network, 1 CPU/1 GiB, non-root uid 65534, read-only `/src`, and fresh `/out` (plus read-only `/in` for audit). Do not use Docker/Podman-compatible runtime commands as a fallback.

## STOP conditions

Stop before candidate if WSLc cannot start, source/image integrity fails, main advances after freeze, another owner has an active conflicting WSLc operation, or output mounts are not fresh/isolated. Preserve exact evidence and report `STOP` (not a scientific FAIL). After the candidate begins, never rerun it under this allocation.
