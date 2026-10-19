# Repository cleanup plan

This plan makes the repository easier to work in with many independent workers while preserving research questions, first outcomes, evidence, ownership, and dependencies. It does not define success as zero open Issues or PRs.

## Execution refresh — 2026-10-20

The earlier count-only checkpoint was at `87dfb33d94f3a8bbe12fbf3ab5bc7f0433c8d8c5`; it returned 1,673 open Issues and 479 open PRs but did not refresh the inventory. A full paginated refresh is now preserved as [r97](maintenance/repository-inventory-20261019-r97.md) at main `4ef4169b28952ff9b546cb1ab19aed74bb5efce0`. The count-only checkpoint is superseded by r97. No remote Issue or PR state was changed for inventory capture.

The user's organizing objective is to make the repository safe for many workers to contribute independently while keeping ideas available for future research. A catalog entry is a way to preserve and connect an idea, not a reason to close its Issue. Close an Issue only after its distinct question, evidence and limits, dependencies, disposition, successor (if any), and reopen condition are recorded. Keep unresolved computer-control goals, active assignments, integration work, and evidence-custody gaps open. Review and integrate PRs as a separate stream; never infer a PR's disposition from its Issue or from an inventory row.

## Fresh live baseline r97 — 2026-10-19 16:00 UTC

The full paginated membership read at main `4ef4169b28952ff9b546cb1ab19aed74bb5efce0` returned 1,673 open Issues and 479 open PRs, matching GraphQL. The Issue and PR ID sets match r96; all PR head/base refs and OIDs also match r96. Exact CSV hashes, capture times, and reproduction commands are in the [r97 inventory](maintenance/repository-inventory-20261019-r97.md). This replaces r96 as the current membership baseline only. It is not semantic classification or current owner/custody evidence; refresh affected live records before dispositions.

### Ordered work waves

1. **Refresh routing facts.** Capture a paginated Issue/PR inventory at one main SHA. Treat it as membership only, then refresh exact source Issues, PR heads/bases, linked evidence, dependencies, and current ownership as each batch is selected. Do not use counts or stale rows to close or reassign work.
2. **Synthesize idea families.** Work in small, non-overlapping batches. For each source Issue, map the hypothesis, sibling distinctions, all material outcomes (including failed, invalid, and inconclusive attempts), evidence/raw links, scope limits, dependencies, and one next decision. Link the family page from the idea index and keep the source Issue as the live discussion/intake record.
3. **Set item-level dispositions.** Keep actionable and blocked goals open with finite exit conditions. Catalog and defer only when the family page preserves the question and a concrete revisit trigger. Mark superseded/completed/out-of-scope only with item-specific evidence and a named successor or rationale. Close individually, after the live Issue receives the source trail; never close a batch to reduce the count.
4. **Review PRs independently.** Refresh each exact head/base and full diff; check unique code/evidence, dependencies, local tests, and actual required protections. Merge only verified changes that advance the objective. Fix, retarget, preserve, or close the rest with a recorded disposition; account for their branches and evidence separately.
5. **Offer disjoint worker packets.** Publish several finite options from different families, each with exact source refs, allowed files, a private output path, dependencies/shared-resource needs, collision boundaries, and an exit test. The map is dispatch guidance, not an assignment or allocation. Serialize edits to shared indexes and this plan through one integrator.
6. **Reconcile physical repository custody last.** Audit branches, registered worktrees, unregistered directories, ignored data, raw evidence, dependent work, and running owners as distinct facts. Remove only items whose exact custody is proven; retain unknown items with a specific unresolved question.

Completion means the open backlog has a traceable classification path, completed family batches are semantically organized, every changed Issue/PR has a defensible disposition, and workers can select independent bounded work. It does not require zero open Issues, zero open PRs, or deletion of old research records.

## Prior full inventory r96 — 2026-10-19 15:22 UTC

The default branch was `b0e47dd4f67a57db5c530d19251ad172e29554d7` before and after the paginated read. GitHub CLI returned 1,673 open Issues and 479 open PRs; GraphQL returned the same totals. The full row sets are preserved in [r96 inventory](maintenance/repository-inventory-20261019-r96.md), [open Issues](maintenance/open-issues-20261019-r96.csv), and [open PRs](maintenance/open-prs-20261019-r96.csv). Both ID sets match r95; r96 refreshes PR head/base OIDs and issue/PR metadata against the newer main. Membership is still not semantic triage, review of every PR diff, or proof of current owner/custody. Re-fetch the exact live item before a state change.

At the time, this was the working baseline for the plan. It is superseded for membership by r97 above; keep r96 and earlier records immutable. The 1,673 Issues need family-level meaning and disposition; the 479 PRs need independent exact-head review. First organize each hypothesis with its existing outcomes, limits, dependencies and a finite next decision. Then retain actionable/blocked Issues or close only individually catalogued ideas with a source link and reopen condition. Continue integrating verified PRs separately; never treat a smaller count as research progress.

## Fresh live baseline r95 — 2026-10-19 14:37 UTC

At the start of the full paginated read, `main` was `97f3d3625c716631858d9eed685c581c7e5aa5fc`. GitHub CLI returned 1,673 open Issues and 479 open PRs; the counts matched GraphQL. Rows and exact PR head/base metadata are preserved in [r95 inventory](maintenance/repository-inventory-20261019-r95.md), [open Issues](maintenance/open-issues-20261019-r95.csv), and [open PRs](maintenance/open-prs-20261019-r95.csv). The PR CSV SHA-256 is `B44F3734273E62016F47752668B0C87D7DCD00E6846EDD0B0AC0648F1F934E9C`; the Issue CSV SHA-256 is `3BB1D84C57AEA2FF2605CA13FF4AD74B87744C6C730197319B2B73E35B72DE89`. The Issue ID set is unchanged from r88. The only PR removed is #9194, verified merged at `97f3d3625c716631858d9eed685c581c7e5aa5fc` at 14:30 UTC. These are inventory facts, not semantic review, ownership, or authorization to change state. Recheck the affected item at decision time.

A fresh local read-only custody count found [26 registered worktrees, 8 changed, and 188 unregistered immediate work directories](maintenance/worktree-custody-overlay-r02-20261019.md). Ignore/process/owner custody remains unknown, so all unregistered folders and changed worktrees stay on HOLD. Do not use clean git status or old names to infer safe cleanup.

The prior r88 snapshot below is retained as history; it is no longer the latest full inventory.
## Prior complete inventory snapshot r88 — 2026-10-19 14:02 UTC

At inventory capture time, `main` was `68a15ed1d50124390e3f88a85829db0f702bd1a8`; a fully paginated GitHub CLI read returned 1,673 open Issues and 480 open PRs; `main` was unchanged before and after the read. The row-level membership and selected metadata are preserved in [inventory r88](maintenance/repository-inventory-20261019-r88.md), [open Issues](maintenance/open-issues-20261019-r88.csv), and [open PRs](maintenance/open-prs-20261019-r88.csv). This replaces r87 as the latest full inventory only. It does not semantically triage any row or establish ownership. The next cleanup work remains family-sized review: connect each idea to its source, existing outcomes/raw, limits, current owner/dependency, and a concrete next decision before changing any Issue or PR state.

The #17 safety-control family is being used as one semantic cleanup batch, not as a reason to mass-close Issues. PR #9192 carries a bounded cancel-response fix and separately hashed r04 Xvfb evidence; the current-head X11 integration run and all reported PR checks pass. The family index, worker map, idea/outcome index, experiment packet, and consolidation history link the scoped result and its limits. PR #9192 is now merged at `3bc02f2b9c7362e743db5f81f3b3d2556038c55f` after every reported check passed. Issue #17 stays open because release certification, task success, bounded recovery, MAP01 and efficiency remain unresolved. The actual current PR state must be refreshed before merging; no global Issue/PR or worktree inventory is implied by this checkpoint.

PR [#9195](https://github.com/Unjuno/agent-interface/pull/9195) then merged the r88 repository membership snapshot and its navigation updates at `9654cbc9c55ce8752d4e7858da3680394753acaf`; no Issue was closed. Current #17 evidence is separately recorded in [r06](../research/integration/standard_caller_xvfb_cancel_trace_20261019/r06/README.md): a post-SIGKILL settle fix now observes exact-child retirement and independent Xvfb key-up readback in the withheld-ack baseline, while API release remains `UNKNOWN`, whole-operation return is 860.150 ms, task success null, and replay denied. The open visual research family remains split among grid (#3), broad design thesis (#4), and addressing/feedback (#5) in its [canonical agenda](ideas/visual-interface-agenda.md); none was closed because it was catalogued. These are scoped cleanup/evidence updates, not a complete semantic audit of all 1,673 Issues and 480 PRs. The r88 counts are a dated inventory snapshot, not present-day membership; refresh current membership and exact ownership before a new state-changing batch.

**#17 latest Xvfb outcome after r88 (PR #9194, run 39268728350):** The [r08 packet](../research/integration/standard_caller_xvfb_cancel_trace_20261019/r08/README.md) preserves a passing current-code rerun after the separate r07 retirement miss. The withheld-ack case returned in 874.924 ms with exact owner retirement, XRes disconnect, independent release-worker readback and all-up parent/horizon keymaps; four ACK-immediate samples also passed their scoped checks. Caller release stays `UNKNOWN`, late request remains possible, `task_success=null`, replay denied; comparison n=2 per mode is diagnostic only. r05–r08 remain immutable and distinct. This Xvfb synthetic-app result does not certify physical release, MAP01/product success, bounded recovery or efficiency. Issue #17 remains open.
## First live PR disposition from r95

PR [#9006](https://github.com/Unjuno/agent-interface/pull/9006) was re-read at head `655a5bcdf6026650044e0157343d4e0de268a548`, base `main`. It is a draft test-only change to `runtime/backends/win32_v1/test_integration.py`; the PR description reports 19 focused helper tests passing locally and 8 Windows-only tests skipped on its local run. Its latest published checks include `native-mcp` and `native-win32` failures, with the latter exposing an unresolved `GetAsyncKeyState == 0` release-verification contract. The PR itself says production code is unchanged and keeps the change in draft. **Disposition: `needs-local-fix` / contract review; keep open and unmerged.** Next finite action is to decide and test the zero-state contract against current main, then rerun the focused and affected Windows suites on the exact updated head. This is a one-PR spot review, not a disposition of the other 478 PRs.
## Verified starting point at r96

At this historical checkpoint, the verified baseline was [r96](maintenance/repository-inventory-20261019-r96.md) at `b0e47dd4f67a57db5c530d19251ad172e29554d7`; r97 above is current for membership. Earlier r87/r51/r52/r95 counts and discovery queues remain immutable historical records. Re-fetch the exact Issue, PR, head, evidence, and current owner before any state change. Routing an Issue to a family is only discovery; it does not finish semantic classification. See the [r51 routing queue](maintenance/open-issues-missing-research-primary-row-20261019-r51.csv), [r52 coverage audit](maintenance/idea-index-coverage-20261019-r52.md), and [consolidation history](REPOSITORY_CONSOLIDATION.md).

**Current checkpoint after cleanup PR #9186 merged:** main is `bee4b22ebc1166d2055b367aff5d363ee82848c7`. A direct GitHub search read at 2026-10-19 12:19 UTC reports 1,673 open Issues and 480 open PRs. This count-only read does not replace a paginated row-level inventory or confirm semantic status. The new [local worktree custody overlay r01](maintenance/worktree-custody-overlay-r01-20261019.md) records the separate workspace scan and its unresolved ownership boundary.

**Current checkpoint after cleanup PRs #9186/#9187 and scoped recovery PR #9185 merged:** main is `547cce6bb9965d8029e9c4478dce20f9ac35a3fb` (2026-10-19 12:35 UTC). A live GitHub search read at 12:36 UTC reports 1,673 open Issues and 479 open PRs. #9186 repaired the documentation entry points and added this operational plan; #9187 recorded worktree custody; #9185 retained a five-attempt standard-caller Xvfb recovery packet. The #9185 scoped path passed with independent key-up readback after explicit recovery and a synthetic property effect, while runtime `task_success` remained null. Its latest evidence-only-head X11 workflow also recorded one separate blocked-cancellation test race; the safe result kept release UNKNOWN and replay disabled. See [PR #9185](https://github.com/Unjuno/agent-interface/pull/9185) and its [retained packet](../research/integration/standard_caller_guarded_recovery_xvfb_20261019/README.md). These counts remain membership only, not semantic or ownership review. The earlier 24-worktree/188-folder custody scan remains the last complete workspace snapshot; ignored data and process ownership were not checked.

**Evidence-catalog checkpoint after PR #9189 (2026-10-19):** the [#17 safety-control family](ideas/safety-control-agenda.md) and [idea index](IDEAS_AND_OUTCOMES.md) now point to the preserved [standard-caller Xvfb trace packet](../research/integration/standard_caller_xvfb_cancel_trace_20261019/r01/README.md). It keeps run 39252995939 (cancel returned before owner retirement, held `a`, cleanup UNKNOWN) distinct from run 39256375123 (owner retired and independent release readback succeeded, but caller still returned UNKNOWN and task_success null). This is one scoped evidence-catalog update, not a full repository baseline refresh or #17 disposition. Re-fetch current membership, exact PR states and worktree custody before further batch decisions.

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

The latest local read-only custody count found 26 registered worktrees (8 with changes) and 188 immediate work directories not registered as worktrees; see [custody overlay r02](maintenance/worktree-custody-overlay-r02-20261019.md). This is a HOLD inventory. It is not permission to delete, and it does not cover ignored files or process ownership.

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
