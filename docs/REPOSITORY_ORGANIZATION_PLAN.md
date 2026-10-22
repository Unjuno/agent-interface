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

## Repository-wide convergence sequence

The six work orders above are performed as finite waves, with the evidence and
ownership needed by a later wave established before state changes:

1. **Freeze the map, not the work.** Refresh complete Issue/PR membership and
   note active allocations, owners, exact branches and unique evidence. Ongoing
   experiments keep their declared boundary; independent audits can continue.
2. **Build a hypothesis catalog.** Route source Issues into canonical families.
   Keep distinct questions distinct even when they share code. Preserve the
   original Issue URL, first outcomes, counterexamples, raw/source identity,
   unresolved question and next discriminating test. Mark idea-only records as
   deferred only after the canonical page and source Issue cross-link each
   other.
3. **Converge PRs on current main.** Classify each open PR as merge-ready,
   bounded repair/retarget, superseded with verified transfer, or evidence/
   dependency hold. Verify exact head/base, changed files, source applicability,
   local checks, unique artifacts and actual repository protections before any
   merge or close. Integrate useful work as soon as these checks pass; do not
   wait for an invented reviewer quota or close a PR just to lower counts.
4. **Set Issue state from the catalog and implementation.** Close scoped work
   only when the recorded result satisfies that Issue's question. Close a
   duplicate only after its unique evidence is represented by the canonical
   family and the source Issue links there. Keep unfinished research and real
   blockers open with one finite next action and a verifiable release
   condition.
5. **Resolve custody and navigation.** Reconcile live branches, worktrees,
   ignored outputs, sessions and experiment packets against merged/current
   content. Preserve uncertain ownership. Then update the entry points and
   publish disjoint worker packets.

Workers may audit separate families or PRs in parallel when their write paths
and evidence are disjoint. One integrator serializes edits to shared indexes;
this is file ownership, not a head-count or approval gate. A repository is
orchestration-ready when every current queue item has an evidence-backed
disposition, every retained artifact has recoverable custody or an explicit
investigation, and independent workers can identify non-overlapping scopes.
Open Issues and PRs may remain when their research or evidence is still live.

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

## Current execution checkpoint after PR #8833 (2026-10-22)

Current main is `2b29ebe0ca6fe8214985a7e50c46a72f5f3af17f`, the fast-forward
integration of PR #8833. The complete [r139 membership recheck](maintenance/repository-inventory-recheck-20261022-r139.md)
confirms 1,655 open Issues and 456 open PRs, with main unchanged across the
paginated reads. The Issue set matches r138. PR membership added #9363 and
removed #7120 and #8833: #7120 was closed as superseded, #8833 merged, and
#9363 opened. The exact sets and sorted-ID hashes are retained in the r139 CSVs.
These counts and check states are discovery aids, not semantic disposition or
merge readiness.

Live reads at capture time show #17, #57, and #7924 OPEN. PR #9363 is an
open, non-draft Win32 operation-owner recovery design that edits the canonical
prestarted-supervisor design and adds two inert-fake schedule packets. Its base
is the pre-#8833 main, while current main is its direct successor; both reported
checks pass and GitHub reports it mergeable. The next bounded batch is an exact
head/base and evidence audit of #9363 against current main, including its
raw-manifest/custody and design-boundary cross-links. Keep the runtime proposal
opt-in and do not merge solely on check status; the audit must establish that
the uniquely useful evidence and current-main applicability are preserved.

The canonical [prestarted supervisor design](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md)
already exists and remains the selected integration thread. Its design and
qualification gates are separate from this membership snapshot. This update
does not consume WSLc/Docker or change any Issue/PR state.

## Historical execution checkpoint after PR #9356 (2026-10-22)

Current main is `5a32f1e486b40103a1f24a6059ae78c8cb884e0f` (PR #9356).
Membership recheck [r138](maintenance/repository-inventory-recheck-20261022-r138.md)
confirms 1,655 open Issues and 457 open PRs. The Issue set is unchanged from
r137; #8827 was closed as superseded after its C02 result was transferred
byte-for-byte through #9356. PR #9356 opened and merged during the interval and
has no net membership effect. These counts are only a queue baseline, not
semantic triage or readiness. The authoritative exact IDs and hashes are in
r138.

Fresh live reads show #17 and #57 OPEN; #7924 is OPEN with its migration STOP
still requiring a current ownership/release receipt. PR #8371 and #9355 are
MERGED; #7290 and #8827 are CLOSED as superseded; #9356 is MERGED at the
current main SHA. PR state changes still require refreshed exact records and
evidence review.

The first PR convergence batch after r137 transferred Issue #8648's C02 finite
synthetic-model result from old-base PR #8827 to current-main PR #9356. No
candidate/auditor was rerun. Fourteen manifest entries match Git blobs; all 15
packet files are blob-identical to the source PR, while the shared analysis
index retains the C02 route along with newer entries. Current-main successor
validation passed with Python 3.13 strict analysis-index and workspace-index
checks and `git diff --check`. The remote checks were queued, but main had no
branch protection or rulesets and the relevant local checks passed. PR #8827
was closed only after merge and transfer verification. Issue #8648 remains
open because the finite model does not answer real route/task feedback.

The separate `work/agent-interface` checkout is on
`integration/x11-fake-socket-relay-r01` at `994f18dcd479eca0885e979749db30073a98f3a2`,
with modified and untracked files across idea indexes, current-goal and
consolidation documents, maintenance receipts, and integration evidence. Its
owner and resume status are not verified. Preserve it and establish custody
before any reset or archive. This makes that worktree a concrete next custody
batch; repository-wide branch deletion is not justified.

**Next bounded batch:** select a small exact-head PR slice from r138, refresh
live metadata/diff/checks and linked Issue, and integrate the first item whose
current-main applicability and local checks pass. The previously refreshed
candidate set includes the evidence-only #8845 and #8833; their WSLc/model/task
limits and unique evidence must be checked before disposition. In parallel only
where paths are disjoint, audit one idea family from the existing semantic-route
queue. Do not start with mass Issue closure or worktree deletion.

## Historical execution checkpoint (2026-10-22; superseded by r137)

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

## PR convergence receipt (2026-10-22)

After the earlier checkpoint, PR [#8371](https://github.com/Unjuno/agent-interface/pull/8371) merged through GitHub at `999c811a6e516f79db357d9a48ed03b1aca50f2c`. Its six-path result preserves bounded report publication/retention and truthful all-attempt model metrics. The exact composed tree was checked against the locally validated candidate; focused custody and metrics tests passed 12/12 in normal and optimized Windows CPython 3.11.9 with Pillow 10.2. Workspace-index, navigation-link, and whitespace checks passed. The broader native runner was attempted locally but did not pass on this Windows checkout: its protocol run recorded 2 failures, 106 errors, and 17 skips, with platform/sparse-checkout incompatibilities; do not describe that suite as green.

PR [#7290](https://github.com/Unjuno/agent-interface/pull/7290) was closed as superseded by #8371 after comparing all six changed paths. Its five report/caller paths match the merged result, and the protocol/harness suite registrations in its branch are already present in current main. The close preserves the source branch, discussion, and historical evidence; no unique code or registration was discarded.

This receipt advances report custody and measurement accounting only. It does not qualify live GUI control, bounded release under blocked platform I/O, MAP01, task-success semantics, matched efficiency/reliability, or WSLc. Issue #7924 remains STOP/HOLD because shared WSLc ownership is unknown; no WSLc allocation or container operation was used. The supervisor design remains opt-in, and its remaining qualification gates stay in the [canonical design page](architecture/PRESTARTED_CANCEL_SUPERVISOR_DESIGN.md).


A paired current-main Fake X regression packet is retained at [r01](../research/integration/fakex_prestarted_supervisor_local_current_main_20261022_r01/README.md), with raw mode-specific logs, structured receipts and SHA-256 manifest. The public-caller and supervisor suites passed 15/15 normally and under `-O`. A helper-only late-resume probe also resumed 16 ms after expiry in each mode and recorded zero effects, one refusal, and `expired_deadline`. This is synthetic helper/caller evidence only; real X-server blocked-I/O release and MAP01 remain unqualified.

## Current-main R02 source audit (2026-10-22)

The retained [R02 standard-caller Xvfb result](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-02/README.md) ran at `cdc8bd6b65bf976137db645c2be31e20090f7d67`, an ancestor of current main `2f971fe867f7c85a82c90d504b1dce9e29534bd5`. A current-main diff over `runtime/cli_v1`, `runtime/guarded_x11_v1`, and `runtime/backends/x11_v1` is empty, and all five files listed in the packet's `raw/runtime-manifest.sha256` match the current checkout byte-for-byte. R02 therefore remains applicable to current runtime source as of this main SHA; this is a source-currency audit, not a new run or a reliability sample.

The result remains one schedule with the owner blocked in `Display.sync()` while the X server can serve the supervisor; whole-server unavailability, physical desktop/MAP01, owner-exclusive XTest state, matched efficiency, and reliability remain unqualified. Its independent task oracle is synthetic, and the canceled operation still has `task_success=null`, `release_confirmed=false`, and replay denied. No WSLc allocation was used.


The independent [R02 raw/source audit](../research/audits/standard_caller_xvfb_r02_raw_audit_20261022_r01/README.md) verified all 17 raw hashes and five runtime source hashes, then reconstructed the 252.924 ms caller response, 324.791 ms supervisor readback, 379.339 ms parent-client readback, and 8.501 s delayed-request horizon from the raw JSON. It also checked distinct target/session/process-generation values and the fresh synthetic task oracle. This confirms the retained one-run outcome and does not add a second sample.

## Current-main R03 Xvfb repeat (2026-10-22)

One independently frozen repeat ran the same standard-caller blocked-`Display.sync()` and fresh-session scenario against main `6b276fcabfa11c060282e0714501a1057e75c0a6` in Ubuntu WSL2 with private Xvfb. The unittest passed 1/1 and Xvfb exited 0. Caller response was 255.100 ms; supervisor readback 323.415 ms; terminal cancellation receipt 329.723 ms; separate parent-client keymap readback 386.460 ms; and the 8.505 s delayed-request horizon found all keys up with no old delayed press. Distinct target/session/process-generation values passed the synthetic fresh-task oracle at input and horizon. The old operation remains UNKNOWN, task success null, and replay denied.

The shell wrapper exited 2 after writing both successful test/Xvfb exit codes because its CRLF-terminated final `exit 0` was parsed incorrectly. This wrapper defect and three preflight-script parsing failures are preserved in [R03](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-03/README.md); none altered the candidate result, and R03 was not retried. The paired R02/R03 outcomes are two observed passes under this one schedule, not a reliability estimate. Whole-server unavailability, physical GUI/MAP01, matched efficiency, and WSLc remain unqualified; no WSLc allocation was used.

## Current-main Xvfb full-process pause boundary R01 (2026-10-22)

A test-only extension to the standard-caller test paused its exact private Xvfb process for 1,500.674 ms. The request returned pending in 253.566 ms from cancellation admission, before Xvfb resumed; pending preserved UNKNOWN/no-release/no-replay. After resume, the supervisor verified release in 59.355 ms and an independent client saw all keys up in 98.039 ms. The delayed-request horizon and distinct fresh-session synthetic task oracle passed. See the [frozen R01 evidence packet](../research/integration/standard_caller_xvfb_current_main_20261022/prestarted-xserver-pause-01/README.md).

This is one paused-Xvfb schedule. It does not prove release while X11 is stopped or establish physical GUI/MAP01, reliability, matched efficiency, or WSLc portability. The runtime result remains UNKNOWN; no task-success or replay promotion follows from the synthetic oracle.

## Matched Xvfb pause pilot and remaining timing gap (2026-10-22)

A six-trial matched pilot on current main `cc5ef16c560cc985ee0951d3d53d659e892f5167` compared three no-pause controls with three 1.5 s pauses of the exact private Xvfb process. All six passed the frozen admission-based caller, release/readback, fresh-generation synthetic task, and old UNKNOWN/no-replay checks. Admission-to-response ranged 253.263–256.398 ms. Paused-arm independent all-up readback followed Xvfb resume by 101.874–127.834 ms. Full conditions, paired results and raw hashes are in the [pilot packet](../research/integration/standard_caller_xvfb_current_main_20261022/paused-server-matched-pilot-01/README.md).

The test timestamp precedes a deliberate 50 ms stop-confirmation wait; it lacks a timestamp immediately before the caller tool invocation. Actual invocation-to-return and exact fresh-effect observation latency remain unqualified. This small three-pair pilot does not establish broad reliability, matched token/model efficiency, release while X11 is stopped, physical GUI/MAP01, or WSLc portability.

## PR convergence follow-through: #7120 (2026-10-22)

At current `origin/main` `31dd17fa83131d3cdf3c4f3703d98015e411e2e5`,
PR [#7120](https://github.com/Unjuno/agent-interface/pull/7120) was an
old-base draft with a conflicting merge state. Its overflow-safe caller-cost
aggregation and focused aggregate/cost-coverage checks are already present on
current main. The retained experiment packet is also present in the current
tree from rescue commit `cb3fb7cea16ab57c5474164dc17b88f7ff51daa9`.
Against the exact current-main source, 21 aggregate and cost-coverage tests
passed in both normal and optimized Python 3.13.14. The stale PR was closed
after this source/evidence check; the original branch, discussion, and saved
results were retained. No experiment or WSLc/Docker allocation was used.

This closes one historical duplicate PR, not the PR queue. The latest complete
membership receipt remains r138 at its recorded older main SHA; no fresh
full-queue count or semantic census is claimed here. Next cleanup batch: refresh
the live queue, then select one open PR with a bounded source/evidence transfer
or a computer-control family with a clearly finite canonical-record update.
