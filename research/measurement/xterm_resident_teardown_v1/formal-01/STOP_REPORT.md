# Formal invocation disposition — STOP before allocation

Issue: #4448, `xterm-resident-teardown-20260927-r1`  
Frozen source commit: `53060eb8c12efdf14a83d0f88969ec93126af0b9`  
Execution: local Docker only; pinned cached image `agent-interface-golden-ipc-2705:20260920-wmctrl` (`sha256:7e4a3b6f3917baa9f153b4dfd011a4ea528a3d200a7a3d274aa9479900ee7b41`); `--pull=never --network none --read-only`.

## Outcome

Disposition: `STOP_FORMAL_OUTPUT_DIRECTORY_COLLISION`. The frozen runner was invoked once, but terminated in `run_all()` while creating its output directory (`pathlib.Path.mkdir(..., exist_ok=False)`) because `/evidence/formal-01` already existed. The host-side invocation had pre-created `outputs/formal-01`; this violated the runner's expected fresh-output-path precondition.

Runner exit code: 1. Exception: `FileExistsError: [Errno 17] File exists: '/evidence/formal-01'`. No pair setup or action execution began; formal pairs/actions: 0/0; no timing rows or `raw.json` were produced. The local host directory is retained as created and is not represented as scientific evidence.

The single frozen invocation has been consumed. No retry, replacement, source/gate/schedule edit, or construction-data pooling was made. The independent formal audit was not run because there is no raw formal evidence to audit. This is an execution-procedure failure, not an experimental result; no performance inference is warranted. Any future attempt requires a separately versioned successor protocol/Issue with an explicit fresh-path procedure and its own source freeze.

## Integrity

The frozen source files and thresholds remain unchanged. Construction-29 remains excluded and unchanged. No GitHub Actions/workflow was used.
