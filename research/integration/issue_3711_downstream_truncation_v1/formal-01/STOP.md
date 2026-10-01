# Allocation 01 — STOP before experiment

- Allocation: `issue3711-downstream-truncation-orbstack-01`
- Frozen base: `2dff80852292cc82fd5c23a449c8244bea94bc25`
- Container: OrbStack Docker, `linux/arm64`, `--network none`, root read-only, source read-only, pinned Python 3.12 image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`.
- Command outcome: process exit 1 before the runner created any attempt/request/report or called its synthetic backend.
- Exact failure: `ModuleNotFoundError: No module named 'runtime.selector_v1'` while importing `runtime.cli_v1.api`.
- Cause: the source worktree was sparse and included `runtime/cli_v1/**` but omitted an import-time runtime dependency. This is harness/source-mount incompleteness, not a candidate result.
- Scientific disposition: `STOP_HARNESS_SOURCE_INCOMPLETE`. No downstream bytes were sent, no JSON consumer was exercised, and no recovery claim is made.
- Preservation: allocation-01 freeze files and this STOP record remain unchanged. It will not be rerun. A new successor allocation must freeze the complete import-time source closure and a new identity before execution.
