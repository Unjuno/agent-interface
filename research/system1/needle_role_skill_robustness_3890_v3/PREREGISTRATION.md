# Pre-registration — Issue #4619

Allocation: `needle-role-skill-robustness-3890-v3-freshblock`  
Branch: `research/needle-role-skill-robustness-3890-v3-20260927-01`  
Base main: `a1a9a7d0abdcdf65d5aba3b74e7f7caf171f2ca4`  
Seeds: 913000, 913100, 913200, 913300, 913400, 913500, 913600, 913700, 913800, 913900.

The full frozen H/T/D/C/U and exact acceptance thresholds are the byte-bound public Issue #4619 snapshot in `ISSUE_CONTRACT.md`. This is a fresh ten-seed successor; no result from #3890, #4479 or #4529 is changed or pooled.

**Single treatment:** fresh seed block only. All model architecture, synthetic task/labels, training and adaptation examples/steps/optimizers, held-out sample sizes, graph semantics, loader protocol, and >=0.90 per-role gate are copied from merged #3890. Each seed owns its data/update stream offsets +1 through +12. New seeds are spaced by 100. Construction asserts all new component streams are pairwise disjoint and disjoint from #3890's 3788–3790 plus #4479's published/retired 3792–4692 and STOP-branch 100000–100900 schedules.

**Formal invocation:** one host orchestration running ten builder + twenty isolated loader Docker containers. CPU-only, one thread, 1 CPU / 2 GiB / 64 PIDs, cached pinned image, network none, read-only root/source/package, 64 MiB /tmp, unique empty per-seed output mounts. Builder argv passes both `NEEDLE_SEED=<seed>` and `NEEDLE_OUTPUT=/out`; source fails closed before fit if either is missing, malformed, out of allocation, or output is not an empty dedicated mount. The Docker argv binding is construction-tested before freeze. No retry, tuning, replacement, exclusion, or post-result change.

Raw package, gzip expected/prediction rows, process logs, loader outputs, immutability receipts, one-shot invocation receipt, source/environment identities, and independent audit are retained. The audit reconstructs the corpus/labels/logits independently without importing runner, loader, or formal orchestration.
