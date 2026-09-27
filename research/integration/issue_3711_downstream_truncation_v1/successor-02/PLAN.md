# Issue #3711 downstream-truncation successor allocation 02

Allocation: `issue3711-downstream-truncation-orbstack-02`.

Base: `2dff80852292cc82fd5c23a449c8244bea94bc25` (main, 2026-09-21).

## H/T/D/C/U

- **H — Hypothesis:** If the actual CLI producer receives a full-accept write result but a downstream transport delivers only an incomplete JSON prefix, the downstream parser rejects that incomplete document. The original retained request/report remain recoverable through the actual read-only `attempt-status` command without dispatch replay.
- **T — Test:** Invoke actual `runtime.cli_v1.__main__.main()` dispatch/presentation once with a deterministic synthetic backend. A bounded sink returns the full character count while delivering only the first 23 UTF-8 bytes. Parse the delivered bytes; then invoke actual `attempt-status` on the same retained run and compare exact request/report hashes and directory contents before/after.
- **D — Design:** One fresh OrbStack Docker run, Python 3.12 `linux/arm64`, pinned image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, `--network none`, read-only root/source and bounded writable output/tmpfs. Freeze the complete top-level import closure: CLI, selector and motor-state source files plus runner/auditor/plan. Preserve the two pre-formal sparse-source construction failures and the successful import-only closure check separately under `../preflight/`.
- **C — Decision:** `PASS_SCOPED_DOWNSTREAM_REJECTION_AND_READ_ONLY_RECOVERY` only if producer reports full acceptance, consumer rejects the delivered incomplete JSON, actual recovery returns `report_recorded` with `replay_allowed=false`, retained request/report hashes and bytes are unchanged, and synthetic dispatch count remains exactly one. Any contradiction is FAIL; infrastructure/harness failure is STOP and will not be retried under this allocation identity.
- **U — Uncertainty/scope:** Synthetic in-process downstream truncation only; not an OS/network proxy, power-loss test, live GUI/effect, or general caller-safety evidence. Producer exit status is reported separately because post-acceptance transport truncation may be invisible to the producer. No runtime source is changed.

## Frozen inputs

`FREEZE.json` binds all source and harness hashes plus image/base identity. `experiment.py` executes the single runner; `audit.py` is run in a separate fresh container against read-only source and result inputs. Runtime changes, model calls, GUI actions, and live tasks are out of scope.
