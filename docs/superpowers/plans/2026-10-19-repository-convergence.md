# Repository Convergence Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` to carry out this plan task by task. Keep each task independently reviewable and record its evidence before moving on.

**Goal:** Make Unjuno/agent-interface legible and safe for parallel work by preserving research ideas and outcomes, assigning every Issue/PR/repository artifact a reasoned disposition, and exposing only bounded, non-conflicting work to workers.

**Architecture:** Keep one short current-state entry point, immutable dated inventories and result packets, and one canonical research-family record per hypothesis family. Triage Issues, PRs, Git refs/worktrees, and local artifacts as separate linked surfaces; close or remove an item only after its meaning, evidence, dependencies, and recovery path are recorded.

**Tech Stack:** Git/GitHub metadata, Markdown family records and work maps, existing local validation commands, and repository evidence packets.

**Spec:** [Repository consolidation policy](../../REPOSITORY_CONSOLIDATION.md); [current goal and evidence boundaries](../../CURRENT_GOAL.md); [research issue index](../../RESEARCH_ISSUE_INDEX.md); [worker work map](../../WORKER_WORK_MAP.md).

## Global Constraints

- Preserve the active computer-control goal as the project objective; this cleanup plan supports it and does not replace or declare it complete.
- Treat local worktree counts as host-specific observations. Distinguish directories, Git-registered worktrees, nested repositories, and ordinary outputs before assigning custody or cleanup.

- Preserve FINAL v5 and all live user assignments; this plan does not allocate or release hardware, WSLc, Docker, accounts, or experiment slots.
- Preserve raw results, first outcomes, source revisions, and historical inventories byte-for-byte; add corrections and later states as new records.
- Organize ideas and evidence before changing Issue state; an Issue may close as catalogued/deferred only after its distinct hypothesis and provenance are findable from the Issue.
- Keep every unresolved user objective, active assignment, custody question, and unverified result open or explicitly blocked with an exit condition.
- Review and merge PRs against their current exact head/base and repository protections; do not invent review-count requirements.
- Do not delete or rewrite branches, worktrees, ignored files, or raw artifacts until exact ownership, dependency, backup, and recovery checks pass.
- A clean repository means every active surface has a traceable disposition and every offered task is independently executable; it does not mean zero open Issues or PRs.

## Review Focus

- A broad Issue overlaps a narrower follow-up without sharing its success criterion; keep the distinct question and successor link explicit.
- A failed, held, or consumed experiment is mistaken for no result; retain its first outcome and prevent accidental reruns.
- An open PR's latest head/base or CI result differs from its saved inventory; refresh before review or merge.
- A clean or detached worktree appears abandoned while an owner, ignored artifact, process, or dependent branch still exists; require custody evidence.
- A candidate worker task shares mutable files, scarce resources, or experiment inputs with another assignment; do not publish both as independent work.

---

## Repository-wide execution sequence

The latest complete row-level historical baseline is [r85](../../maintenance/repository-inventory-20261019-r85.md), captured 2026-10-19 09:22–09:25 UTC on main `b1bff75ffa5d06f6d2c7d10bc7a89b1ab2dbdc16`: 1,673 open Issues and 482 open PRs. The host-specific [orchestration snapshot](../../maintenance/repository-orchestration-snapshot-20261019-r01.md) records a later 1,673/480 membership observation after #8799 and #8781 merged, but is not a new complete row-level export. Treat both as immutable dated evidence; refresh live state immediately before a disposition and do not infer issue meaning, ownership, or cleanup eligibility from counts.

### Task 1: Establish a fresh, reproducible baseline

**Files:**
- Create: `docs/maintenance/repository-inventory-<date>-rNN.md`
- Create: `docs/maintenance/open-issues-<date>-rNN.csv`
- Create: `docs/maintenance/open-prs-<date>-rNN.csv`
- Modify: `docs/REPOSITORY_CONSOLIDATION.md` with one link to the newest baseline and current phase

- [x] Capture all open Issue and PR pages from one named main commit; include timestamps, total counts, stable sorted-ID hashes, and exact PR head/base, author, assignees, labels, checks, and merge state.
- [x] Validate pagination completion, unique IDs, row counts, and CSV hashes; compare membership with r70 and explain every transition without overwriting r70.
- [x] Record baseline command/source, capture time, commit, and validation output in the snapshot note.
- [x] Pass when the note and both row-level exports reconcile exactly and can be read without relying on live GitHub state.

### Task 2: Reconcile repository files and evidence custody

**Files:**
- Create or update: `docs/maintenance/repository-surface-map-<date>.md`
- Update: `docs/WORKER_WORK_MAP.md` only after artifact owners and destinations are known

- [ ] Inventory tracked root/documentation entry points, research-family records, runtime packages, generated outputs, local-only artifacts, and archived/history directories.
- [ ] For each duplicate or stale-looking document, identify its canonical successor and preserve a redirect or historical link before proposing archival.
- [ ] Reconcile local worktrees, branches, ignored/untracked files, running processes, saved outputs, and open PR/Issue dependencies; mark unknown ownership as a hold with the next evidence needed.
- [ ] Pass when every observed repository/workspace artifact has a canonical location, a linked owner/work item, or an explicit custody hold; no deletion is required for this pass.

### Task 3: Organize research ideas into canonical families

**Files:**
- Create or update: `docs/ideas/<research-family>.md`
- Update: `docs/IDEAS_AND_OUTCOMES.md` and `docs/RESEARCH_ISSUE_INDEX.md`

- [ ] Group by hypothesis and success criterion, not by age, author, or Issue number. Keep adjacent but non-equivalent hypotheses as separate rows/families.
- [ ] For every family, link source Issue IDs, distinct hypotheses, strongest simple baseline, existing positive/negative/held results, raw and source revisions, unresolved counterexamples, dependencies, and the smallest next experiment that could change the decision.
- [ ] Mark consumed allocations and prohibit reruns; distinguish construction checks, method evidence, live caller evidence, task effects, and end-to-end comparisons.
- [ ] Pass when every research Issue in the current snapshot resolves from the index to exactly one primary family record (or an explicit multi-family mapping) and every family record links back to its source Issues.

### Task 4: Triage every Issue by meaning and next action

**Files:**
- Create: `docs/maintenance/issue-disposition-<date>-rNN.csv`
- Update: relevant family records, the research issue index, and `docs/WORKER_WORK_MAP.md`

- [ ] Assign each Issue one primary disposition: `keep-open/actionable`, `keep-open/blocked-with-exit-condition`, `catalogued/deferred`, `superseded`, `completed-scoped`, or `out-of-scope`; record secondary tags separately.
- [ ] For every keep-open Issue, state the concrete next discriminator or completion criterion, dependency, owner/assignment evidence, file/resource scope, and whether a worker can start now.
- [ ] For idea-only deferrals or duplicates, first publish the canonical idea/family link and provenance in the Issue; then close individually with the reason, successor, and reopen condition.
- [ ] Leave live objectives, assigned/consumed experiments, unintegrated results, and unresolved custody/ownership questions open until their own exit criteria are met.
- [ ] Pass when all IDs from Task 1 have one reviewed disposition and no closure depends only on age, missing comments, or reducing the count.

### Task 5: Review and converge open PRs independently

**Files:**
- Create: `docs/maintenance/pr-disposition-<date>-rNN.csv`
- Update: disposition records and linked Issue/family entries as needed

- [ ] Refresh each PR's exact head/base, unique diff, commit dependencies, current checks, local verification needs, author/worktree custody, and linked evidence immediately before a disposition.
- [ ] Classify each PR as `merge-ready`, `needs-local-fix`, `stack/retarget`, `evidence-custody-hold`, `duplicate/superseded`, `owner-confirmation-hold`, or `close-after-preservation`.
- [ ] Integrate independently useful fixes and scoped results when actual protections and local checks pass; retain failures/limits and report the resulting commit in the family record.
- [ ] Close a PR only after preserving any unique code/evidence and identifying its successor or reason; do not close merely because its Issue closed.
- [ ] Pass when all snapshot PRs have a current reviewed disposition, every merge/close has a traceable reason, and no open PR's only next step is unknown.

### Task 6: Reconcile branches, worktrees, and workspace artifacts

**Files:**
- Create: `docs/maintenance/ref-worktree-disposition-<date>.md`
- Add custody links to the corresponding Issue/PR/family record

- [ ] Compare each local and remote branch tip with open PR heads, bases, successor commits, and recoverable commits; record dirty, ignored, and untracked content separately.
- [ ] Confirm worker/session ownership and artifact role for every noncanonical worktree or output; stop only processes whose owner and purpose are known.
- [ ] Archive or remove only artifacts whose contents are preserved, refs are recoverable, no active owner/dependency remains, and the disposition is recorded.
- [ ] Pass when every extant worktree/ref/output is canonical, active, safely archived, or explicitly held with a named evidence requirement.

### Task 7: Publish a parallel-work-ready queue

**Files:**
- Update: `docs/WORKER_WORK_MAP.md` and `docs/WORKER_QUICKSTART.md`

- [ ] Offer only items whose hypothesis, exact repository scope, dependencies, entry revision, tests, evidence outputs, resource needs, stop conditions, and exit artifact are explicit.
- [ ] Mark file-level and resource-level conflicts so concurrent workers receive disjoint scopes; route shared-file integration through one named integrator.
- [ ] Keep assignments and current user goals authoritative; the map is a discovery queue and cannot grant experimental resources or override a live assignment.
- [ ] Pass when a new worker can select one item and produce a reviewable result without choosing a research question, guessing a baseline, or colliding with another worker.

### Task 8: Verify convergence and maintain it

**Files:**
- Create: `docs/maintenance/repository-convergence-report-<date>.md`
- Update: `ROADMAP.md`, `docs/REPOSITORY_CONSOLIDATION.md`, and the worker map to point to the report

- [ ] Reconcile the final Issue/PR IDs and disposition counts to Task 1; report remaining open work by family, actionable next step, blocked exit condition, and owner evidence.
- [ ] Verify each active PR/worktree/ref and each retained experiment packet has a recovery path; list unresolved custody holds plainly.
- [ ] Run relevant local documentation/data integrity checks and validate all newly added links; use local checks for required validation rather than treating optional remote CI as a universal gate.
- [ ] Pass when no active item is orphaned, no research idea or outcome is lost, worker scopes are conflict-aware, and the report names the exact remaining work required for the next convergence pass.
- [ ] Add a lightweight rule to the worker quickstart: every new Issue/PR/result enters the canonical index/family and gets a disposition link at creation or integration time.

## Recommended execution order

Complete Task 1 first. Tasks 2 and 3 can then run over disjoint repository areas; Task 4 depends on family records for research Issues. Task 5 can proceed in disjoint PR batches after its fresh baseline, with shared-file or stacked PRs kept together. Task 6 must not remove anything until Tasks 4–5 establish dependencies and Task 2 establishes custody. Task 7 publishes only completed, conflict-checked slices. Task 8 is the completion gate. The active computer-control objective remains intact throughout and its experimental allocations are governed by its own current assignments.
