# Historical candidate #5639 evidence custody

This is an archival preservation of the old guarded-control/public-caller candidate and its stacked retained-analysis audit. It does not adopt the old runtime implementation or change the meaning of any historical result.

## Exact provenance and scope

- Original [candidate #5639](https://github.com/Unjuno/agent-interface/pull/5639) head: `7e3a7b6f8310a64c2a6ce4c6d75a29b458ebba08`
- Original [audit #5653](https://github.com/Unjuno/agent-interface/pull/5653) head: `546c6e3237e1d5455657071115ac330e06f274d4`
- Main baseline for this preservation tree: `9f8e281750bd3be8c8dcd1bfb966bc45afa353f6`
- [Machine-readable custody inventory](CUSTODY.json) accounts for all 196 candidate result files and all five stacked-audit files
- The planned integration commit retains both original heads and the main baseline as parents. No branch reset, force push, branch deletion or rewriting of prior outcomes is part of this preservation

Production code, workflows and other existing main files stay at the main baseline. The sole existing-file edit is an additive pointer in [the results index](../README.md).

## What is preserved, and where

The archival addition contains 118 exact original files from 18 result namespaces plus the five exact #5653 audit files. Git blob identity, byte length and SHA-256 are recorded individually in CUSTODY.json.

Another 35 files are already present at the same main paths with identical Git subtrees: [activation-review-01](../activation-review-01/README.md), [activation-review-02](../activation-review-02/README.md), [guarded-activation-01](../guarded-activation-01/README.md) and [guarded-focus-transfer-01](../guarded-focus-transfer-01/README.md). They are not duplicated.

Another 43 original files are already retained byte-for-byte as members of three main archives. Data-only checks read every regular member and verified the outer inventories, then matched each of these 43 members to its original Git blob:
- guarded-pointer-move-01 and reference-lifetime-01 are inside [hover-lifetime-main-01](../hover-lifetime-main-01/README.md)
- primary-input-self-use-01 is inside [primary-helper-main-01](../primary-helper-main-01/README.md)
- post-release-feedback-01 is inside [post-release-main-01](../post-release-main-01/README.md)

The inventory gives the exact containing archive, member path, Git blob, byte length and SHA-256. These four original directory copies are deliberately not duplicated at top level.

## Two additive audits, one retained original failure

The original [spine-02](../post-release-spine-02/README.md) raw archive, manifest, analysis and v1 verifier remain unchanged. Its original order-sensitive comparison failure is retained, not relabeled as a successful v1 run.

The candidate's [separate v2 auditor](../post-release-spine-02-audit-v2/README.md) and #5653's [AUDIT_V2.md](../post-release-spine-02/AUDIT_V2.md), analyze_v2.py, verify_v2.py, test_audit_v2.py and audit-v2/verification.json are both preserved. They share refusal-inventory-only canonicalization but are distinct artifacts. #5653 retains additional end-to-end mutation tests. Neither historical test suite was executed for this preservation.

## Runtime and scientific disposition

The old runtime was integrated selectively through #5724, #5786, #5815, #5838, #5852, #5861, #5871 and #5888. Later #6496, #6506 and #6512 are also present on the main lineage. The custody inventory records their merge commits. This preservation imports no old product behavior.

Historical STOP/HOLD/FAIL and narrowly scoped PASS outcomes remain as written, including incomplete integrations, first failures, image-presentation limitations, terminal cleanup qualifications and unmeasured model/economic boundaries. No result is retried, pooled, repaired or promoted.

[Issue #57](https://github.com/Unjuno/agent-interface/issues/57), [#59](https://github.com/Unjuno/agent-interface/issues/59) and [#2789](https://github.com/Unjuno/agent-interface/issues/2789) retain their separate acceptance requirements. Administrative PR disposition is not scientific completion.

## Validation and execution limits

Preservation validation is limited to exact artifact bytes, Git-tree composition, inventory coverage and newly added navigation. No archived source, verifier, experiment, container, GUI, input or model was run. Historical commands and relative links remain unedited; some require the original pinned checkout and must not be mistaken for current-main validation instructions.

Ordinary hosted execution is intentionally not used for this archival delivery. Both the preservation-head publication and any eventual main-merge commit must use GitHub's documented `[skip actions]` directive after a fresh mandatory-check review. Skipped or absent checks are not reported as passed. No required check is bypassed and no workflow is disabled.
