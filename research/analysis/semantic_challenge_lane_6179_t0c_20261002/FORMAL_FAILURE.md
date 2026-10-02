# Pre-formal resource STOP — T0c

Allocation `6179-T0C-EXECUTED-BROKER-CONTROLS-20261002-01` is terminally stopped before formal WSLc execution. WSLc construction containers: 0; WSLc candidate containers: 0; WSLc auditor containers: 0; retries: 0; formal WSLc raw output: none. The construction rung was not consumed.

## Evidence and disposition

- Microsoft WSLc 3.0.1.0 is available. Read-only `wslc list --all --format json` showed only exited containers at the pre-run check.
- The shared repository worktree inventory nevertheless contains concurrent WSLc/GPU research allocations (`research/gpu-six-worker-memory-sharing-4972-wslc-a10-20261002`, `research/gpu-six-worker-memory-sharing-4972-wslc-a10c-20261002`, and CUDA repair work). No authoritative release/lease-clearance for the shared host was available. An empty container inventory is not proof that another owner has released the host.
- The separate #6471 T0 has now completed and been integrated into current `main` as a `PASS_METHOD_SCOPED` synthetic method result. It is no longer the blocker.
- Host-only construction: `python -m unittest -v test_protocol` — 9/9 passed. The synthetic JSON round-trip audit returned `PASS_METHOD_SCOPED`, 18 rows, zero errors. These remain development checks, not WSLc/formal evidence.
- The WSLc-only `build_check.py` was mistakenly invoked twice on the Windows host. Each printed `memory.max=MISSING` and `CONSTRUCTION_STOP`, exit 2, before running tests. Neither created a container.
- A mistaken `python candidate.py --help` call treated `--help` as the output filename and executed the candidate once on the Windows host. The unmodified 58,960-byte raw output is retained as `HOST_DIAGNOSTIC_CANDIDATE_RAW.json`, SHA-256 `9d656fcd8cab175353054fd7dcefabc2b084ea2ec6678ba1efbf1b149f8d62b1`, with 18 rows. It is not a formal WSLc result. This consumed the allocation's one-shot candidate invocation budget outside the required environment, so the candidate must not be rerun in WSLc and the independent formal audit was not started.
- Host diagnostic commands/output, the raw hash, source/image identity checks, and the two construction-gate stops are retained in the task execution history; no WSLc container was created.

Disposition: `STOP_PRE_FORMAL_ONE_SHOT_CANDIDATE_BUDGET_CONSUMED_OUTSIDE_WSLc`, not a scientific FAIL. No Docker, Podman, GPU, network, user data, live verifier, or external effect was used. Preserve this terminal outcome; do not retry this allocation or relabel the host candidate as WSLc evidence.
