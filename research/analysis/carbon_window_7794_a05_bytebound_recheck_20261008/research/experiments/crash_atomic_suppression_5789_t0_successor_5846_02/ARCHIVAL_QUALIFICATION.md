# Archival qualification: allocation-02 start-gate STOP

Prepared 2026-10-02 from original PR #5931 head `c3e5cbe64d7780d50742f390e2f11b564d165615`.
This package preserves the consumed allocation-02 start gate. It is not a scientific result or permission to resume the historical allocation.

## Retained outcome

The terminal receipt `results/5846-02/STOP.md` records `STOP_MAIN_ADVANCED_AFTER_FINAL_FREEZE`: final local source `82ea141a508f208117f5bc416fdeaf795a611087`, then refreshed main `80289fb745883f7264a752434319333adee41f69`, failed exact-current-main gate, candidate/auditor invocations 0/0, retries 0. The reported isolated guest was stopped and retained. The process-crash hypothesis was not evaluated. The [owner outcome notice](https://github.com/Unjuno/agent-interface/issues/5846#issuecomment-5930847679) describes the same pre-candidate provenance failure using the label `STOP_MAIN_ADVANCED_BEFORE_CANDIDATE`; neither record is rewritten here.

`README.md`, `FREEZE.md`, and `CONSTRUCTION.md` retain prospective preparation commands and gate language from before the STOP. They are historical instructions for a consumed allocation, not a present authorization. No frozen manifest is regenerated and no guest, Docker runtime, candidate, auditor, model, GUI or scientific test is launched by archival review or integration.

## Verification limits and immutable bytes

The original 14 package files reconstruct their published Git blob identities. All 12 entries in the original `SHA256SUMS` match the retained bytes; its scope is the original source/freeze/construction inventory. The later terminal STOP receipt is not listed in that frozen manifest and remains a separate preserved original blob. This qualification does not add itself or the receipt to the historical manifest.

The original eight Python files parse as syntax and `FREEZE.json` parses as data. These static checks do not import or execute the archived code. The package's historical 23/23 host construction-test report, earlier 19/19 and inherited 15-row rehearsal claims, compilation, index and runtime observations remain author-reported; this review did not independently rerun those behavioral checks. Hosted CI is a separate repository-check fact and does not reproduce the package tests or create scientific evidence.

## Owner and predecessor boundaries

Allocation-01 is a distinct consumed `STOP_MAIN_ADVANCED_AT_FORMAL_START_GATE`, retained through PR #5896 at `research/experiments/crash_atomic_suppression_5789_t0_successor_5846/results/5846-01/PREFLIGHT_STOP.md`. Allocation-02 does not duplicate, replace, retry or pool that evidence. Issue #5795's earlier `STOP_FORMAL_ARGV_MISMATCH` and its 0/0 counts likewise remain unchanged. This package's source is self-contained; predecessor links are evidence lineage, not an instruction to execute or modify predecessor packages.

Issue #5846 remains open. This archive does not establish crash-atomic safety, power-loss behavior, multi-writer serialization, product authority, or a current resource lease. Any future scientific attempt needs a distinct allocation, current-main source freeze and new additive output namespace; none is created here.
