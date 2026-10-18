# Repository consolidation restart r28 — 2026-10-19

This is a current restart point for the repository-wide consolidation plan, not a claim that every open Issue or PR has received semantic review.

## Current membership check

A cursor-paginated GitHub CLI read at approximately `2026-10-18 20:11 UTC` returned 1,675 open Issues and 514 open PRs for `Unjuno/agent-interface`, against `main` `92dca0df6022fd50b2b439e6863cf2a4da05851f` (PR #9070). Compared with the complete r22 metadata snapshots, the Issue ID set is unchanged; the only PR ID removed from the open set is #9064. The r22 CSVs remain immutable historical snapshots from before that merge; this recheck is membership only and does not create a new metadata snapshot or claim semantic triage.

| Surface | Current count | Change from r22 | Meaning |
|---|---:|---|---|
| Open Issues | 1,675 | no IDs added or removed | Membership only; bodies, ownership and idea coverage still need family-level review. |
| Open PRs | 514 | #9064 removed | #9064 merged; the remaining PRs are not classified by this count. |

## Confirmed integration transition

- [PR #9064](https://github.com/Unjuno/agent-interface/pull/9064) merged at `9202407ff031f36c7b68221f3d7d3af0924417ca`. It added PID-qualified XRes evidence; its private-Xvfb result is bounded to the recorded responsive topology.
- [PR #9068](https://github.com/Unjuno/agent-interface/pull/9068) merged at `ec4d3f9417c6da2156fa2af79bda9503348c1602`, passing the owner PID into the standard MCP path and failing closed if it is unavailable.
- [PR #9069](https://github.com/Unjuno/agent-interface/pull/9069) merged at `49ef83ab62f6523a4baa3980226e17e780441ef7`, updating the work map and evidence links.
- [PR #9070](https://github.com/Unjuno/agent-interface/pull/9070) merged at `92dca0df6022fd50b2b439e6863cf2a4da05851f`. Its standard-caller regression now asserts that the owner PID reaches the supervisor; late queued DOWN still leaves release UNKNOWN. This strengthens the caller contract but does not establish a real-server queue fence, physical release, bounded release deadline, independent task effect or general recovery.

Issue [#17](https://github.com/Unjuno/agent-interface/issues/17) and Issue [#57](https://github.com/Unjuno/agent-interface/issues/57) were confirmed open. The #17 result does not satisfy #57's integrated efficiency requirement. No WSLc allocation was used for this membership check.

## Consolidation rules and next batch

The outcome requested by the user is a repository where ideas stay discoverable and workers can take independent, reviewable work. It is not an empty Issue list. Preserve each distinct hypothesis and historical result, including failed or inconclusive outcomes. Mark missing review `untriaged`, and missing experimental support `unverified`; connect each reviewed idea to its source Issue, current evidence and limits, dependencies, next finite test, and the decision that test can change.

Continue from the current coverage-gap queue in the [worker map](../WORKER_WORK_MAP.md) and [idea index](../IDEAS_AND_OUTCOMES.md), one research family at a time. Before closing an Issue, verify its acceptance condition or document an evidence-backed duplicate transfer/rejection; a real successor must retain unresolved work and be usable. Before merging a PR, read its live head/base, unique evidence, relevant local checks and actual protection state. Before deleting a branch/worktree, verify its exact tip, dirty/untracked files, active owner/process, open-PR dependencies and evidence custody. Keep unknowns visible rather than converting them to closure.

For many workers, assign disjoint Issue/PR families, source areas and additive output paths. Serialize changes to shared indexes. Do not make complete semantic review a prerequisite for independent research; leave the unreviewed remainder as a bounded queue and keep its count/time basis explicit.

This recheck closed no Issue, merged no PR, and removed no branch, worktree or raw evidence. Repository-wide idea and PR disposition remains in progress.
