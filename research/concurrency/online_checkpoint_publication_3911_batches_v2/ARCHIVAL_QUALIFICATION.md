# Archival qualification: #3992 three-batch checkpoint publication

This is a **freeze-and-status record only** for [Issue #3992](https://github.com/Unjuno/agent-interface/issues/3992) and [Draft PR #4028](https://github.com/Unjuno/agent-interface/pull/4028). Evidence delivery remains **`HOLD_PUBLICATION_INCOMPLETE`**. Preserving the available hash commitment does not recover its referenced source, raw, construction or audit corpus and does not independently reproduce the reported scientific result.

## Exact source preserved

- Source branch: `research/checkpoint-publication-3911-batches-20260922`
- Source head: `024d20dd93aae5adf56bdedc8e8ed3370548ab9b`
- Original package tree: `3ac0a079c5d8fbf74ed10079ac2840e6feb8e8d7`
- Only source file: [`FREEZE_V2.json`](FREEZE_V2.json), preserved at its original path without byte normalization
- Git blob: `d5215c9d9176cfca27bc2f581497d724d7e4f59b`; stored bytes: **3,737**
- SHA-256: `4b565d06d5870c50d297caa50e7217e2daf00c1e8189aa616f8a17be7225174a`

The source PR has one changed file. Its complete package tree contains only this freeze file. The locally fetched bytes match both the Git object ID and the [public freeze comment's SHA-256](https://github.com/Unjuno/agent-interface/issues/3992#issuecomment-5766628674). The freeze contains **29 hash commitments**, not 29 delivered files. The referenced plans, environment, inherited sources, wrappers, construction outputs and predecessor ZIP are not present in that package tree. No missing content is reconstructed from hashes or prose.

The JSON's `formal_batches_started: 0` is the preserved pre-execution state, not current unused capacity. Its commands are historical commitments, not instructions or permission to run again. The allocation was subsequently reported consumed and completed once.

## Historical scientific result, explicitly reported

The [first-outcome report](https://github.com/Unjuno/agent-interface/issues/3992#issuecomment-5766719713) identifies allocation `checkpoint-publication-batches-20260922-02`: **three immutable 42-case batches**, 126 cases total, with all three actual exits reported as zero and no timeout or rerun. It reports `PASS_LOCAL_PROCESS_CRASH_PUBLICATION_SCOPED` for finite, read-only checkpoint availability:

- DIRECT_FINAL: 9 valid-old, 36 valid-new and 18 correctly refused incomplete latest checkpoints
- ATOMIC_RENAME: 45 valid-old, 18 valid-new and 0 incomplete latest checkpoints
- All 18 NORMAL controls valid-new; all 126 reads non-authoritative
- Raw auditor: 4,449 checks, zero errors; batch-envelope audit: 85 checks, zero errors
- 12 raw-evidence and 8 batch-envelope corruption controls reported rejected

Those statements are retained historical reports. This archive has not restored or independently re-audited the raw evidence. The published result identities are useful recovery targets, not proof that their bytes are available here:

| Reported target | SHA-256 |
|---|---|
| Original row ledger, 42,333 bytes | `ee98fd7de766d791004726b793c321c5b03df41e9abe322dcc90e90f16adaefb` |
| Full audit JSON | `4fd2faacc702bf30e66d7619f424f325c88dfb378f47345c636bdb5e320511e9` |
| Raw corruption controls | `c7275f702e3962d30f6d611e3bd67ae260ad8b7d3879b6d73f59638fb57632f1` |
| Batch corruption controls | `e3739254777552c6e7d17da02241addc9d73d071a0aab8d2c697ba8b11a89d9c` |

The original report also retains a failed tool-session polling incident while the independently supervised experiment continued without relaunch. Its per-batch elapsed times are budget diagnostics, not a performance comparison. No historical outcome is revised here.

## Earlier outcomes and distinct allocation remain separate

The original [#3911](https://github.com/Unjuno/agent-interface/issues/3911) learning/logit and update-latency **FAIL** remains unchanged. The predecessor allocation `local-checkpoint-publication-3911-20260922-01` retains `STOP_OUTER_EXECUTION_TIMEOUT`, 20 completed / 1 partial / 105 unstarted cases, and its original HOLD audit. Its declared 298,888-byte ZIP SHA-256 is `867427c3117ea28c7abe22c51db764f57574dd7f04cfece7432478c7388d2ebf`. That ZIP is a historical recovery target, not a recovered artifact in this archive. No rows or allocation capacity are pooled, resumed, replaced or rerun.

The distinct **nine-by-14** allocation `local-checkpoint-publication-3911-20260922-02` is recorded by merged [PR #4287](https://github.com/Unjuno/agent-interface/pull/4287), in neighboring [`online_checkpoint_publication_3911_v2/`](../online_checkpoint_publication_3911_v2/). Its `PUBLICATION_NOTE.md` and `RESULT.json` were present on the inspected main with blobs `78c0133aae12d015eaaa47a4ba2ed6feb06546ce` and `40b3c4ec8ce78254e6e0c96bd5307d9ae3835f09`. Its raw-bundle HOLD remains; its 2,129-file ZIP and audit counts are not the three-batch evidence. Equal aggregate counts do not make the allocations interchangeable. The [2026-09-30 clarification](https://github.com/Unjuno/agent-interface/issues/3992#issuecomment-5907506843) records that the nine-batch branch name returned 404; recreating a pointer would not recover absent raw bytes. This archive does not alter that branch or its records.

## Why preserve this record

At inspected main `f346b787a5a31381f51c0b7bd19740c3c7380db7`, the complete `research/concurrency/` tree had no `online_checkpoint_publication_3911_batches_v2/` directory and no copy of this freeze blob. The existing concurrency index lacked this study. Its distinct nine-batch summaries were already retained. Targeted PR/code searches and the inspected archive namespaces did not identify another three-batch freeze archive; these are bounded coverage checks, not proof about every unpublished workspace or unreachable object.

This preservation adds the exact one available blob at its original path, this separate qualification and one existing-index entry. It introduces no source changes, new result artifact, replacement research question or new formal allocation. The frozen JSON is not edited to encode later status.

## Continuing delivery gate

The [owner's routing update](https://github.com/Unjuno/agent-interface/issues/3992#issuecomment-5770614838) and [later recovery review](https://github.com/Unjuno/agent-interface/issues/3992#issuecomment-5859597547) keep #4028 Draft and preserve its branch. Archival preservation does not release that gate, make the source PR merge-ready, close #3992 or authorize cleanup.

- **H:** the exact original three-batch evidence can be made reachable from a committed branch
- **T:** if those bytes become available, attach them under the existing #3992/#4028 delivery track and verify fixed-commit byte identity, bounded restoration and independent read-only re-audit; never rerun the consumed allocation
- **D:** delivery remains `HOLD_PUBLICATION_INCOMPLETE` until the exact source/raw/construction/audit corpus and bounded restore/readback path satisfy that gate
- **C:** a freeze hash, aggregate result, CI success, partial archive or different allocation cannot establish completeness or reproduce the reported result
- **U:** the available record cannot establish raw validity, source/process/phase lineage or complete byte restoration; missing publication is not a new scientific FAIL

Retain the stated finite-fixture limits: synthetic checkpoint bytes, explicit split-write/barrier fault injection, highest-final-name read-only recovery, one writer, same-directory rename and successful fsync assumptions. SIGKILL is not power loss; readable or complete-but-unacknowledged bytes grant no resume, replay or action authority. There is no evidence here for trained-state recovery, multiple writers, real disk/power-loss durability, ACK-loss-safe continuation, cross-platform/engine transfer, model quality, 60 ms latency, production promotion or global ROADMAP completion.

No retained script, test, auditor, model, container, writer, reader or formal allocation was executed for this preservation. Verification was limited to read-only GitHub metadata/file retrieval and local byte/hash/tree/text checks. Future publication repair stays with the existing question under [`ISSUE_FAILURE_CLASSIFICATION.md`](../../../docs/ISSUE_FAILURE_CLASSIFICATION.md).
