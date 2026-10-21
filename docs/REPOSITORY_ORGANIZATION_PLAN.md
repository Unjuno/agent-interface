# Repository organization plan

**Purpose:** make `Unjuno/agent-interface` understandable and safe for many
independent workers while preserving every distinct research idea, result,
owner, and recovery path. Organization enables computer-control research; it
does not replace or complete that research.

This is the short execution plan. The [cleanup ledger](REPOSITORY_CLEANUP_PLAN.md)
and [consolidation record](REPOSITORY_CONSOLIDATION.md) retain historical
snapshots and detailed receipts. Never rewrite a historical result to make the
current repository look cleaner.

## What “organized” means

- Each live research Issue has a distinct hypothesis, current evidence and its
  limits, dependencies/owner or an explicit unknown, a finite next step, and a
  reason to remain open or a verified successor/disposition.
- Each open PR has a current exact head/base, a known diff and local validation
  plan, linked Issue, unique code/evidence custody, dependencies, and a concrete
  disposition: integrate, repair/retarget, preserve on hold, or close after
  verified transfer/supersession.
- Every useful branch, worktree, process/session, ignored output, and raw packet
  has a recoverable owner/custody record. Unknown custody is retained and
  investigated; it is never treated as disposable.
- A worker can select one bounded item, see its writable paths and dependencies,
  produce a reviewable result, and update a shared index without overlapping
  another worker. Shared indexes have one integrator at a time; family and PR
  audits can proceed independently when their records and paths do not overlap.
- Entry points direct readers to current work and canonical idea/evidence
  records. Duplicate navigation can be removed only after inbound links and
  unique content are checked.

An empty Issue/PR queue is not the success condition. The condition is that each
record has an evidence-backed disposition and remaining research is easy to
resume.

## Work order

1. **Establish the live queue.** Fetch complete paginated open Issue and PR
   membership, record the main SHA before and after, and compare with the latest
   full snapshot. Reuse unchanged row metadata; refresh only additions,
   removals, and records selected for action. Membership counts are not semantic
   review, ownership, or merge readiness.
2. **Route ideas by family.** Work in bounded batches from the existing idea
   discovery and exact-URL queues. For each candidate, read the live Issue,
   related PRs, canonical family record, and cited first outcomes. Record the
   specific question, strongest simple comparison, supporting and contradicting
   evidence, unresolved residual, dependency, and smallest discriminating next
   test. Keep similar but distinct hypotheses separate. A link or summary alone
   does not count as semantic disposition.
3. **Resolve PRs against current source.** For one PR or a proven disjoint
   group, refresh exact head/base, diff, checks, reviews, linked Issue, branch
   ancestry, and unique evidence. Run the appropriate local checks on the exact
   source. Integrate useful, applicable work when actual repository protections
   permit. Transfer and hash-check unique work before closing a superseded PR.
   Keep unresolved research and evidence-custody holds open with a concrete
   release condition. Do not use fixed reviewer counts or merge to reduce the
   queue size.
4. **Disposition Issues from evidence.** Keep actionable questions open with
   one finite next test; keep blocked questions open with the real dependency
   and release condition; link duplicates to a canonical record only after
   confirming the hypothesis is the same; close scoped-complete or superseded
   records only after preserving the result and return path in the catalog and
   Issue. Never bulk-close by age, label, or inactivity.
5. **Reconcile custody.** Audit branches, registered and unregistered
   worktrees, sessions/processes, ignored outputs, and raw packets after their
   owners and dependencies are known. Verify exact tips, unique changes,
   manifests/hashes, and recovery before archiving or deleting an item. Unknown
   owner or recoverability means retain and investigate.
6. **Repair navigation and enable parallel work.** Update README/current-goal,
   roadmap, worker map, family indexes, and research entry points after their
   targets are verified. Give each work packet a narrow scope, allowed writable
   paths, evidence source, output location, dependency, and completion receipt.
   Resolve conflicting guidance at its canonical source rather than adding
   another policy layer.

## Batch protocol

Each batch selects one family, PR, or custody slice and leaves a compact receipt
with: source SHA and live-record timestamp; records and files inspected;
decision and its evidence; changed paths; local checks; preserved unique data;
open dependency; and the next bounded batch. Do not duplicate full inventories
when only a delta is needed. Do not rerun a consumed experiment to make its
record easier to classify.

Before changing an Issue or PR state, refresh its live body, comments, state,
head/base, checks, dependencies, and owner. Before integrating, check the exact
diff against current main, run relevant local validation, and verify actual
branch protections. Optional CI may be reported as pending; do not wait for it
when local evidence is sufficient and repository protections allow progress.

## Current execution checkpoint (2026-10-22)

The latest complete membership recheck is [r130](maintenance/repository-inventory-recheck-20261022-r130.md),
captured on 2026-10-22 JST against main
`976d36443548e02d169b0b44fab6877224464be4` after PR #9316 merged. It records
1,655 open Issues and 462 open PRs; only #9316 left the open set since r129.
This is a historical membership-only pointer. Current main has since advanced
through PR #9322 to `6430d6e5d79a083bd8dd1cfdadfcd88359587a07`; a
new complete membership snapshot has not yet been recorded. PR #9315 is open
and Draft at head `76626da8b03df25024d12efb5f1dde2f12c53ed2`. The user
selected the prestarted-supervisor design as the first work item; its current
implementation and evidence boundary are reconciled in the [design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#design-review-checkpoint-2026-10-22).
The standard-caller supervisor Xvfb run now covers one supervisor-owned
resource-base reuse, release/readback, delayed-request horizon, and independent
synthetic task oracle. Its runtime receipt remains UNKNOWN and replay denied;
fresh-target recovery and the bystander negative path through the public caller
remain open. Keep the supervisor default-off. Then resume the semantic-route
queue with one bounded family batch. Do not start a broad close/merge campaign from counts alone. A
disjoint exact-head PR audit or custody slice can proceed only when it does
not share edited indexes, branches, or evidence with those items.

The computer-control work remains the research objective. Cleanup must not
launch or consume WSLc/Docker allocations; Issue #7924 remains STOP/HOLD for
shared WSLc ownership. PR #9320 integrated the opt-in supervisor, #9321
preserved its initial evidence, and #9322 reconciled the design. A scoped
standard-caller Xvfb packet records release/readback and an independent task
oracle, while runtime task success remains null and replay stays denied. Keep
#17 and #57 open while recovery, task semantics, efficiency, and safety gates
remain. After this evidence is indexed, resume idea-family disposition;
the remaining route count is a discovery queue, not a closure target.

## Completion checks

This plan is fulfilled when a fresh membership pointer exists; every processed
family/PR/Issue has a traceable disposition; every retained artifact has known
custody or an explicit investigation item; canonical entry points are current;
and workers can claim independent packets without conflicting instructions or
shared-file edits. Report remaining unreviewed records and research gaps
explicitly. “Clean” never means deleting ideas or hiding unresolved science.
