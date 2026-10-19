# Repository cleanup plan

This plan makes the repository easier to work in with many independent workers while preserving research questions, first outcomes, evidence, ownership, and dependencies. It does not define success as zero open Issues or PRs.

## Verified starting point

At main commit `1d95e48e67783fd05b96346c975f9875bc483ce1` (2026-10-19), GitHub search reported 1,673 open Issues and 479 open PRs. This is a live membership count, not a semantic audit, ownership check, or full PR review. The latest complete row-level inventory is [r87](maintenance/repository-inventory-2026-10-19-r87.md), captured at an earlier main SHA; recheck membership and exact heads before any state change. Existing routing work covered 491 Issues missing a historical research-index primary row, but routing is not semantic classification. See the [r51 routing queue](maintenance/open-issues-missing-research-primary-row-20261019-r51.csv), [r52 coverage audit](maintenance/idea-index-coverage-20261019-r52.md), and [consolidation history](REPOSITORY_CONSOLIDATION.md).

**Current checkpoint after cleanup PR #9186 merged:** main is `bee4b22ebc1166d2055b367aff5d363ee82848c7`. A direct GitHub search read at 2026-10-19 12:19 UTC reports 1,673 open Issues and 480 open PRs. This count-only read does not replace a paginated row-level inventory or confirm semantic status. The new [local worktree custody overlay r01](maintenance/worktree-custody-overlay-r01-20261019.md) records the separate workspace scan and its unresolved ownership boundary.

**Current checkpoint after cleanup PRs #9186/#9187 and scoped recovery PR #9185 merged:** main is `547cce6bb9965d8029e9c4478dce20f9ac35a3fb` (2026-10-19 12:35 UTC). A live GitHub search read at 12:36 UTC reports 1,673 open Issues and 479 open PRs. #9186 repaired the documentation entry points and added this operational plan; #9187 recorded worktree custody; #9185 retained a five-attempt standard-caller Xvfb recovery packet. The #9185 scoped path passed with independent key-up readback after explicit recovery and a synthetic property effect, while runtime `task_success` remained null. Its latest evidence-only-head X11 workflow also recorded one separate blocked-cancellation test race; the safe result kept release UNKNOWN and replay disabled. See [PR #9185](https://github.com/Unjuno/agent-interface/pull/9185) and its [retained packet](../research/integration/standard_caller_guarded_recovery_xvfb_20261019/README.md). These counts remain membership only, not semantic or ownership review. The earlier 24-worktree/188-folder custody scan remains the last complete workspace snapshot; ignored data and process ownership were not checked.

The immediate repository-level defects are narrower and verifiable:

- `REPOSITORY_CONSOLIDATION.md` had grown into a dated append-only log and its execution-plan link was broken; this change restores the link and adds a shorter operational plan.
- Historical inventory and routing snapshots are easy to mistake for current semantic status.
- Idea routing receipts cover discovery, while many Issues still need family-level meaning, evidence, ownership/dependency, and next-decision review.
- Issue closure, PR integration, and branch/worktree cleanup are different operations but are discussed in the same long history.

The existing catalog and evidence are useful and stay in place. This plan adds a short operational layer; it does not move raw experiment files or rewrite historical outcomes.

## Canonical record layout

| Information | Canonical home | Rule |
|---|---|---|
| Current objective and operating boundaries | [`CURRENT_GOAL.md`](CURRENT_GOAL.md) | Current direction; update only when direction changes. |
| One finite, non-overlapping work item | [`WORKER_WORK_MAP.md`](WORKER_WORK_MAP.md) plus the live source Issue/PR | Map is navigation, never an assignment or resource grant. |
| Idea, hypothesis, counterexamples, status, next discriminating question | One relevant page under [`ideas/`](ideas/README.md), indexed by [`IDEAS_AND_OUTCOMES.md`](IDEAS_AND_OUTCOMES.md) | Family page distinguishes sibling hypotheses and links source Issues and evidence. |
| Executed result, raw, conditions, audit, limitations | Original packet under [`research/`](../research/) and its [integration reports](../research/integration/) | Preserve first outcomes and bytes; catalog pages link to them. |
| Membership, exact PR heads, checks and review state | Dated inventory under `maintenance/` | Snapshot only; re-fetch before mutations. |
| Process, chronology and cleanup receipts | [`REPOSITORY_CONSOLIDATION.md`](REPOSITORY_CONSOLIDATION.md) | Keep concise current summary at the top; append dated receipts, do not repeat policy. |

Do not create another index when a canonical page already covers the question. If a record needs correction, make an additive correction with source and scope; do not silently rewrite a historical PASS/FAIL/HOLD/STOP.

## Execution sequence

### 1. Freeze a usable baseline

Record main SHA, fully paginated open Issue/PR membership, exact PR head/base and dependency relations, and the date of the read. Treat this as routing metadata only. For each batch, recheck only the live Issues, PRs, comments, branches, evidence, and owners that its decision touches. An empty assignee field, old timestamp, draft status, or open state is not proof that work is unowned or obsolete.

### 2. Organize ideas by research family

Select a small, coherent family from the routed queue or an existing family page. For each source Issue, record:

- the distinct question or hypothesis and its relation to sibling Issues;
- preserved positive, negative, invalid, and inconclusive results, with exact evidence links;
- current implementation/PR/experiment state and limits of the evidence;
- owner, dependency, or an explicit unknown that must be resolved before touching shared resources;
- the smallest next test or integration decision that could change the conclusion.

Use family-sized batches, typically 3–10 related Issues; reduce the batch when comments, evidence, or ownership are complex. Routing-only rows remain marked as routing-only until this review is done. Do not turn an idea into a closure merely because its summary was copied into the catalog.

### 3. Decide each Issue after its idea is preserved

Choose one explicit disposition per Issue: `keep-open/actionable`, `keep-open/blocked-with-exit-condition`, `catalogued/deferred`, `superseded`, `completed-scoped`, or `out-of-scope`. Before closure, update the live Issue with the family/catalog link, preserved outcome and evidence, reason for closure, successor if any, and concrete condition for reopening. Keep open any user goal, unfinished research, implementation, integration decision, evidence-custody gap, or active assignment that still has work. Never mass-close by label, age, or count.

### 4. Integrate PRs separately

For each PR, re-fetch the exact head/base, changed files, current checks and required protections; inspect its full diff, comments, stack, unique result, and linked Issue. Record one next action: `merge-ready`, `needs-local-fix`, `stack/retarget`, `evidence-custody-hold`, `duplicate/superseded`, `owner-confirmation-hold`, or `close-after-preservation`. Run the relevant local checks and satisfy actual repository protections. Do not add an invented reviewer-count gate. After merge/close, verify that code and unique evidence remain reachable from main or a named preserved location.

### 5. Reconcile branches, worktrees and repository structure

Treat remote branches, local directories, registered Git worktrees, ignored artifacts, and running processes as separate inventories. Before removing any item, verify its exact tip, unique commits, untracked/ignored data, raw evidence, dependent work, current process/owner, and recovery copy. If any owner or custody fact is unknown, retain it and record the specific question. Remove duplicated navigation only after the canonical destination is correct and all inbound links are updated. Do not bulk-delete work directories based on names or age.

The latest worktree scan found 24 registered worktrees (7 with changes) and 188 adjacent immediate work directories not registered as worktrees; see [custody overlay r01](maintenance/worktree-custody-overlay-r01-20261019.md). This is a HOLD inventory. It is not permission to delete, and it does not cover ignored files or process ownership.

### 6. Make the work queue safe for orchestration

Every selectable packet must name a family or exact PR set, read-only source refs, permitted files, a private output directory, dependencies/shared-resource needs, and one finite exit test. Parallelize only disjoint families or exact PR sets with separate output paths. Serialize edits to shared indexes and the worker map through one integrator at a time. This enables independent software/document work; it does not grant live GUI, WSLc, GPU, or other shared-resource allocations.

## First bounded work batch

The pilot is complete as a semantic review: [safety/control receipt r01](maintenance/repository-cleanup-family-safety-control-r01-20261019.md) revalidated six live Issues (#2/#10/#14/#15/#16/#17), preserved their distinct research questions and scoped results, and recorded one finite next decision per Issue. All six remain open because each has unresolved research or an explicit dependency. The GitHub assignee field was empty, but no ownership conclusion or reassignment was made. No allocation, branch, PR or Issue state was changed. This receipt is not a complete PR/worktree custody audit and does not claim the rest of the repository has been semantically reviewed.

After the pilot, select the next family from the remaining routing queue using changed research value and unblock potential, not numeric Issue order. Workers can take disjoint family batches while the integrator serializes edits to the shared indexes.

A read-only A07 custody cross-check in [PR #9181](https://github.com/Unjuno/agent-interface/pull/9181) found the independent audit package internally checksummed and its manifest digest cross-referenced, but the private raw bundle needed to reproduce the 2,358-entry claim was unavailable in inspected tracked sources. Keep Issue #59 open and PR #8702 in draft `evidence-custody-hold`; do not rerun consumed A07 or claim MAP01/task success. Revisit only when the unchanged raw bundle or an adequate privacy-approved verification manifest is supplied.

## Completion criteria

Repository cleanup is complete when:

1. The current docs entry points lead to existing, authoritative documents and clearly label historical snapshots.
2. Every open Issue/PR is discoverable from a current live inventory or a declared unreviewed queue; completed semantic batches link each item to its question, evidence, limits, owner/dependency, and next action.
3. Every closed Issue has a preserved catalog/source trail and an explicit disposition; no unresolved goal or evidence-custody task was closed for housekeeping.
4. Every merged/closed PR has its unique code/evidence and branch/worktree custody accounted for separately.
5. The worker map offers multiple disjoint, finite packets with private outputs, and does not imply ownership or live-resource grants.

Open Issues and PRs may remain as an intentional, well-indexed research backlog. Do not claim a complete repository-wide audit until every live membership row and required semantic/custody decision has actually been checked.
