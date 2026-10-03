# Issue #6655 / PR #6694 incomplete preregistration custody

Dated 2026-10-02. This archive preserves eight known published preregistration blobs, not recovered host execution evidence. It makes no scientific result or completeness claim. PR #6694 remains Draft.

## What is actually preserved

The [original/](original/) files are byte-for-byte copies of the package at commit [226b426305e37eabb5bbbccd27b22478a74d4467](https://github.com/Unjuno/agent-interface/commit/226b426305e37eabb5bbbccd27b22478a74d4467) on `research/issue6655-incidental-state-t0-20261002`. The original repository root was `research/analysis/incidental_state_legacy_6655_t0_20261002/`. [ORIGINAL_PATH_MAP.json](ORIGINAL_PATH_MAP.json) records each original/stored path, Git blob, byte count, observed SHA-256, and available recorded source digest. The eight files total 26,610 bytes.

The original README, CONSTRUCTION, preregistration, and freeze remain verbatim historical documents. Their pre-run 0/0 wording is not a final allocation status and must not be treated as permission to execute. None of the archived Python files was run for this preservation.

## Consumed host allocation and missing evidence

[Owner correction 5951176251](https://github.com/Unjuno/agent-interface/issues/6655#issuecomment-5951176251) reports that host allocation `INCIDENTAL-STATE-LEGACY-6655-T0-20261002-01` consumed candidate/auditor/retry counts **1/1/0**, despite [the preceding WSLc start gate](https://github.com/Unjuno/agent-interface/issues/6655#issuecomment-5951136862). That disposition remains unchanged. The owner-reported host PASS does not establish protocol-conforming WSLc evidence; there is no rerun, refreeze, relabeling, or successor authorization here.

The source tip has only the eight preregistration files. Its PR commit timeline contains the preregistration and source-freeze commits; it does not supply the host REPORT, RESULTS, raw outputs, or process receipts claimed by the earlier PR description. Bounded review of the linked owner records and remaining incidental-state branches did not locate an exact recoverable host-result commit. This is a recovery limitation, not proof that no original copy exists elsewhere.

Still needed from the original owner:
- Host candidate bytes matching the reported SHA-256 `a79c5a5c1cf63caa6b4349b2f1987335705e180ccc12ec27c7a64ab43aefa2f6`
- Original host auditor output and process receipts, rather than substituted successor artifacts
- The qualified host REPORT.md and formal_01_20261002/RESULTS.md described in [archival comment 5951471712](https://github.com/Unjuno/agent-interface/issues/6655#issuecomment-5951471712)
- Exact pre-run source/manifests or an explicit account of their unavailability

An identical reported auditor-output digest in another allocation does not prove host-process provenance. No output is reconstructed, synthesized, rerun, or copied from the WSLc successor to fill these gaps.

## Published bytes do not satisfy their recorded source hashes

Readback of these exact Git blobs finds mismatches for all four Python sources and PREREGISTRATION.md against the original FREEZE.json entries. The original freeze and source files are retained unchanged; no line-ending conversion was used to manufacture matching bytes.

| File | Recorded in original freeze | SHA-256 of preserved Git bytes |
|---|---|---|
| PREREGISTRATION.md | `2ddd05cdbe66f2a5156e11337799c9882fc463219fbf5605508e4087a55ddbba` | `4ff2d4a40d9386ed9560ef101b67d302a92839c2182df87775679606dcaa2ef0` |
| audit.py | `2eaa0445f70b8a47240dc6797725044d34be974285cedd8bf2f191a5351d201e` | `e5f71dbeb6efc065741db755493f63c6f8c9fd4572f0042adf7e8655253daa09` |
| candidate.py | `cc807a04eb653ed770736dfde78183ddad344506197a041b761e45c42f7db4ba` | `e2cc2e28833bd224231f24897c53a6874c7bca9425347cea2d2e641d134825f5` |
| fixture.py | `a89ccf8711c2a0aebe12a4d39204517cb325b2ce90162e27a34f7d503f1c8575` | `b315045e906f8f3728d888fb0145a4370c3aa4fdaca750189323934de39e32e7` |
| test_t0.py | `0c947f3d1981fa4f191606dc0984b2fe67cd76e75503bb05270053b17e3b2ee2` | `1077af2d9d5b9049f84f175498ed6676e00bcab8930d271463873d8ee9786e41` |

The owner also described later FREEZE.json byte drift. This snapshot does not supply a separate expected pre-run digest for FREEZE.json itself, so this archive records its observed identity without claiming that missing comparison was verified.

## Preserve the WSLc successor separately

At main `9a327d0511f02c7b8ebd175e20f96a43028578ca`, the original directory name is occupied by the distinct WSLc successor allocation `INCIDENTAL-STATE-LEGACY-6655-T0-WSLC-20261002-02`, delivered through [PR #6690](https://github.com/Unjuno/agent-interface/pull/6690) and [PR #6698](https://github.com/Unjuno/agent-interface/pull/6698). Its FREEZE, PREREGISTRATION, REPORT, RUN_RECORD, code blobs, and results subtree are retained unchanged by this repair. The two allocations are not pooled.

This uniquely named custody directory avoids overwriting the newer allocation. The original commit remains in branch ancestry and original paths remain explicit in the mapping. The repository analysis index links this as preregistration custody outside the generated retained-result block; no REPORT.md or STOP.md was invented to imply a recovered result.

## Publication and execution boundary

The draft synchronization uses `[skip actions]` to prevent unrelated historical research workflows from being triggered by the old-to-current push diff. Source-head and current-main workflow definitions were inspected for uncontained triggers. This is containment, not a CI pass; new-head CI remains unverified. No experiment, candidate, auditor, model, GUI, container workload, promotion, merge, issue closure, tag, or branch deletion is part of this preparation.
