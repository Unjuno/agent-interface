# V3 one-shot execution record

- Allocation: `5309-TOPOLOGY-DEPENDENT-A11-POSTRUN-STRATA-V3`
- Frozen source commit: `82a6a10e0e133ae22294d9e828abb62af0c2e8b9`
- Invocation count: one V3 audit-script invocation; no retry.
- Candidate/environment/formal auditor invocations: zero.
- Output files: `result.json` and `stdout.json`, each 1,111 bytes and byte-identical.
- SHA-256 for each output: `2f7f4270c9e3ac33045a92fe24fd7e0e9a29cdc910f7140e3f8c78f97edf0e40`.

The frozen Python command was invoked with the listed inputs/output. The shell command additionally attempted to copy `$?` into a variable named `status` and then exit with it. In zsh, `status` is read-only; after the Python process had returned and written both output files, the assignment emitted `zsh:1: read-only variable: status`. The outer shell therefore returned exit 1. The Python process's exit status was not captured independently and must remain unknown; it is not inferred from the JSON payload.

No second invocation or shell-based rerun was made. The result payload itself reports `PASS_RETAINED_STRATA_RECONSTRUCTION`, 264 rows, no reconstruction errors, and no unsupported completions. Because the frozen run wrapper returned nonzero and the script exit status is unavailable, the allocation-level disposition is STOP, not PASS. The raw output is retained unchanged for a separately authorized offline review if needed.

No formal A11 stage was rerun. The original formal A11 `FAIL_AUDIT_MISSPECIFIED_STRATUM_GATE` and all V2 artifacts remain unchanged.
