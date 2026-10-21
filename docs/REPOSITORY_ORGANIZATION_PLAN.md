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

This checkpoint records main `3e46261966957f0852703ededb4b6fb2f3a594bf`,
after PR #9346 and the current-pointer refresh. The retained R02 Xvfb trial ran against source
`cdc8bd6b65bf976137db645c2be31e20090f7d67`; its results are historical and
remain tied to that exact source. The latest complete paginated membership receipt is
[r136](maintenance/repository-inventory-recheck-20261022-r136.md), captured at
this main SHA: 1,655 open Issues and 460 open PRs. Its Issue set matches r135;
its PR set differs by the merge of #7181, with #9346 opened and merged between
captures. Counts establish membership only, not semantic disposition. Refresh a
complete set when the next change requires it, and refresh every touched record
before state changes.

The prestarted-supervisor design remains the selected integration thread. Its
standard-caller Xvfb evidence and limits are recorded in the
[design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#design-review-checkpoint-2026-10-22).
The new [R02 trial](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-02/README.md)
passed once against its frozen source: the cancellation response returned pending in
252.924 ms; the supervisor release readback completed in 324.791 ms; independent
key-up readback was observed in 379.339 ms; and a distinct fresh session passed
its synthetic task oracle through an 8.501 s horizon. The old runtime result
remains UNKNOWN, `task_success` null, and replay denied. This qualifies one
same-Xvfb fresh-session recovery schedule, not reliability. The public-caller
Fake X bystander-reuse refusal passes in normal and optimized mode; see its
[separate packet](../research/integration/local_fakex_public_bystander_refusal_20261022_r01/README.md).
The live-Xvfb bystander negative path and whole-server-unavailable release
remain unqualified. Keep the supervisor default-off. The next
science/integration batch must target an explicit remaining gap; do not repeat a
consumed run or turn cleanup into a WSLc/Docker allocation.

PR [#7181](https://github.com/Unjuno/agent-interface/pull/7181) is now merged
and preserves a native P01 three-arm comparison for #57. Its report records
persistent input+output of 39,329 tokens versus 109,373 plain and 111,226
ephemeral, plus ready-to-independent-oracle times of 27.712, 36.631 and 46.550
seconds. Eighteen effects were independently checked, with one bounded repair.
The disposition remains HOLD: each arm has one sample, one fixed-order six-task
fixture/domain, and model/cache/host-load confounding. It is a useful measured
input, not the matched current-caller/second-domain integrated qualification or
a reliability estimate. Keep #57 open and carry these limits into the next
matched integration decision.

Repository-wide execution stays on the six work orders above: establish a live
queue when needed; preserve and route one bounded idea family; resolve exact
PRs against current source; disposition Issues individually from evidence;
reconcile custody only after owner/recoverability checks; then repair entry
points and issue non-overlapping work packets. Start from the
[cleanup ledger](REPOSITORY_CLEANUP_PLAN.md) and
[consolidation history](REPOSITORY_CONSOLIDATION.md), using them as receipts,
not as proof that old counts or assignments remain current. The next cleanup
batch is one refreshed family or exact-head PR slice with a named writable
surface and a short disposition receipt. No bulk close/merge by age, label,
count, or inactivity; no fixed reviewer quota. A disjoint audit may proceed
only when it does not edit the same shared index, branch, or evidence.

The computer-control work remains the research objective. Cleanup must not
launch or consume WSLc/Docker allocations; Issue #7924 remains STOP/HOLD for
shared WSLc ownership. PR #9320 integrated the opt-in supervisor, #9321
preserved its initial evidence, #9322 reconciled the design, #9323
preserved a scoped standard-caller Xvfb result, and #9329 added a bounded
worker-exit grace with a separate retained Xvfb outcome. That run missed the
strict 300 ms caller-response target by 1.268 ms and correctly kept the runtime
receipt UNKNOWN; see the [design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#additive-shutdown-grace-result-2026-10-22).
PR #9331 added a 25 ms response handoff margin. A separate Xvfb run then
returned in 276.447 ms, with independent key-up readback and a passing
synthetic task oracle; runtime status remains UNKNOWN and replay denied. See
the [updated design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md#standard-caller-xvfb-after-handoff-margin-2026-10-22).
The packet records release/readback and an independent task oracle, while
runtime task success remains null and replay stays denied. Keep
#17 and #57 open while recovery, task semantics, efficiency, and safety gates
remain. Continue family disposition from a refreshed current queue; the
remaining route count is a discovery queue, not a closure target.

## Completion checks

This plan is fulfilled when a fresh membership pointer exists; every processed
family/PR/Issue has a traceable disposition; every retained artifact has known
custody or an explicit investigation item; canonical entry points are current;
and workers can claim independent packets without conflicting instructions or
shared-file edits. Report remaining unreviewed records and research gaps
explicitly. “Clean” never means deleting ideas or hiding unresolved science.
