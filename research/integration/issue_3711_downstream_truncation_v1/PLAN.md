# Issue #3711 downstream-truncation experiment

Allocation: `issue3711-downstream-truncation-orbstack-01`

Base: `2dff80852292cc82fd5c23a449c8244bea94bc25` (main, 2026-09-21).

## H/T/D/C/U

- **H — Hypothesis:** If the CLI's stdout writer reports that it accepted the complete JSON document but a downstream transport delivers only a strict prefix, the downstream JSON consumer will reject the incomplete document. The retained request/report pair will still permit read-only recovery without another dispatch call.
- **T — Test:** Run the actual `runtime.cli_v1.__main__.main()` dispatch/presentation path with a deterministic synthetic backend and a bounded sink that records the complete accepted write but delivers only its first 23 UTF-8 bytes. The sink returns the full character count to the producer. Then parse what the downstream received and invoke the actual `attempt-status` CLI command against the same retained attempt.
- **D — Design:** One fresh allocation, current-main source frozen by SHA-256, OrbStack Docker Python 3.12 image pinned to `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` (`linux/arm64`), `--network none`, read-only source mount, read-only root with writable `/tmp` and result mount. Save full accepted bytes, delivered prefix, parser outcome, CLI exit code, request/report bytes and hashes before/after recovery, dispatch call count, and exact source hashes. A separate fresh container runs the independent auditor.
- **C — Decision:** `PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY` only if the sink accepts the full write, downstream receives a strict incomplete prefix and rejects JSON, the CLI's raw report remains recorded and byte-identical through `attempt-status`, recovery reports `report_recorded`/`replay_allowed=false`, and the synthetic dispatch count remains exactly one. Any contradiction is a scoped FAIL; harness/container failure is STOP, never a scientific result.
- **U — Uncertainty/scope:** This is a synthetic in-process downstream truncation boundary, not an OS/network proxy, power-loss durability test, live GUI action, or evidence that arbitrary callers parse JSON safely. The producer cannot observe truncation after a write reports full acceptance; its exit code is recorded, not treated as proof of delivery. No runtime source is modified by this allocation.

## Frozen implementation inputs

See `FREEZE.json` for script/source hashes and exact image identity. `experiment.py` is the sole runner; `audit.py` independently recomputes acceptance from raw files and outputs. The output directory is new and allocation-specific.
