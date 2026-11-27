# Repository open-work membership recheck r83 — 2026-10-19

Captured at 2026-10-19 07:19 UTC from GitHub's complete open-PR listing and
GraphQL open-issue/open-PR counts for `Unjuno/agent-interface`, at main
`640dba3eff3dbb5568da0504f8a624ac80f73c1a`.

| Surface | Open count | Change since r70 | Evidence |
|---|---:|---|---|
| Issues | 1,673 | no membership change | GraphQL count; r70/r71 ID membership remains unchanged. |
| Pull requests | 484 | 5 fewer; no additions | Complete paginated `gh pr list --state open --limit 1000` ID set compared with r70 CSV. |

The PRs no longer open since r70 are #8825, #8811, #8803, #8798, and #8794.
#8825, #8803, #8798, and #8794 are merged; #8811 was closed after its A09
evidence package, all recorded hashes, and analysis-index entries were verified
as already present on main through #9012/#8794. There are no new open PR IDs
relative to r70. The five-item delta is membership evidence only; it is not
semantic triage, ownership confirmation, review of all remaining PR diffs, or
permission to remove branches/worktrees. The latest full row-level metadata
remains the immutable [r70 inventory](repository-inventory-20261019-r70.md).

PR #8803's A06 packet was rebased onto current main and merged at 2026-10-19
07:18:57 UTC. Its preserved result is a pre-start HOLD: the exclusive result
directory already existed, candidate/auditor/OCR counts were zero, and no
experiment was rerun. Construction tests passed 3/3 normally and under `-O`,
all frozen input/source/output hashes verified, and the analysis index was
verified sorted, unique, and complete (854/854). This does not resolve Issue
#1998 or establish a scientific result.

The recheck and A06 integration are recorded in
[consolidation r83](../REPOSITORY_CONSOLIDATION.md#実行更新-r83--a06記録を統合しmembershipを再確認).
Issues remain open unless their individual idea, evidence, successor, and
disposition are recorded; this inventory closes none.
