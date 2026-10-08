# Execution record

Formal allocation was executed once on 2026-09-30 in OrbStack Docker 29.4.0 (`linux/aarch64`) using the image digest and frozen commands in [PLAN.md](PLAN.md). Image filesystem was read-only, network disabled, CPU limited to 1, memory to 256 MiB, pids to 64, all Linux capabilities dropped, and no-new-privileges enabled. Source bind mount was read-only; only `raw/formal/` was writable.

The frozen `experiment.py` formal invocation exited 0. It emitted 18,432 shared exogenous input rows and 55,296 policy rows (24 replicates × 192 steps × four regimes × three policies). No model, live GUI, real action, external network, or task-effect endpoint was involved.

Raw-only audit v1 executed once and exited 1 with `FAIL_RAW_AUDIT`: all decision rows matched, all 4/4 mutation controls were rejected, but the summary cross-check disagreed on only the stationary no-fault signal denominator. That first failure is retained unchanged at `raw/formal/audit.json`.

After documenting and freezing the narrow audit-only correction, audit v2 executed once against the same immutable inputs/outcomes and exited 0 with `PASS_RAW_AUDIT_V2`, `errors=[]`, and 4/4 mutation controls rejected. It wrote a separate `audit_v2.json`. Neither the experiment nor any raw input/output was rerun, altered, or replaced. The audit correction is not additional scientific evidence.

## Commands

The full exact experiment and audit commands, including isolation flags and mounts, are recorded in [PLAN.md](PLAN.md). No retry was made for the formal experiment or either auditor invocation.
