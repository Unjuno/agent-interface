# Repository cleanup worker dispatch r01

**Baseline:** main merge `5efe7301f6e655a41c4653b3c6baf45138ca72f6` (2026-10-19).
These are three independent, bounded work packets derived from read-only audits
of Issues #17, #5, and #59. They are available work, not exclusive assignments
or resource grants. Before starting, a worker must re-read the current Issue,
exact PR head, and target output path; report if any changed. The integrator
owns shared indexes and the consolidation plan and applies each accepted result
serially.

## Shared handoff contract

Each worker returns one additive packet at its named output path containing:

1. the exact main SHA, Issue state/body/comment timestamp, relevant PR number and
   exact head SHA used;
2. source/result links and raw custody status, with every PASS/FAIL/STOP/HOLD
   kept at its original scope;
3. the unresolved predicate and a finite next action that can change a decision;
4. ownership, dependency, and resource facts explicitly marked `unknown` when
   they were not verified;
5. validation performed and limits. Never create a new Issue, close an Issue,
   change a PR/ref/worktree, claim an allocation, or rerun a consumed candidate
   as part of these packets.

Workers use separate output files and do not edit `WORKER_WORK_MAP.md`,
`IDEAS_AND_OUTCOMES.md`, family agendas, or this dispatch file. After packet
review, one integrator updates those shared entry points and this plan in a
single serial change. If an artifact or owner cannot be verified, record the
missing item and stop at that boundary; do not infer loss or permission.

## Packet A — #17 input release and safe recovery

**Question:** What is established by the current standard-caller path when a
blocked input request is canceled, and what is still required to distinguish
owner disconnect, separate release/readback, late queued input, and task effect?

**Read:** Issue [#17](https://github.com/Unjuno/agent-interface/issues/17),
PRs [#9134](https://github.com/Unjuno/agent-interface/pull/9134),
[#9136](https://github.com/Unjuno/agent-interface/pull/9136),
[#9153](https://github.com/Unjuno/agent-interface/pull/9153),
[#9062](https://github.com/Unjuno/agent-interface/pull/9062),
[#9068](https://github.com/Unjuno/agent-interface/pull/9068),
[#9074](https://github.com/Unjuno/agent-interface/pull/9074),
[#9076](https://github.com/Unjuno/agent-interface/pull/9076),
[#9077](https://github.com/Unjuno/agent-interface/pull/9077), and the existing
release evidence packets linked from the Issue and worker map. Compare the
current standard MCP caller tests with the separate A11 Xvfb result; do not
combine their claims.

**Deliver:** `standard-caller-release-crosswalk-20261019-r01.md`. State what is
shown by the Fake X caller composition, what A11 shows only on Xvfb, the
late-request/server-ordering gap, and whether the existing Fake X fixtures can
distinguish: disconnect observed followed by separate release/readback; owner
still connected or unknown; and a late queued press after cleanup. If a missing
case needs implementation, specify a local Fake X test only. User authorization
for Fake X construction checks does not authorize WSLc, Docker, a live desktop,
or a new formal allocation. Preserve A02/A03/A11 first outcomes and raw.

**Exit:** one reviewable evidence crosswalk and, if applicable, a small local
Fake X test proposal with exact test/function scope. No live experiment, no
release-success claim, and no task-success claim.

## Packet B — #5 target identity and visual feedback

**Question:** Which #5 target-binding predicates have evidence beyond Fake X,
and what is the next supported-application boundary?

**Read:** Issue [#5](https://github.com/Unjuno/agent-interface/issues/5),
`docs/ideas/visual-interface.md`,
`docs/ideas/visual-interface-agenda.md`, the “Target binding and feedback” row
in `docs/WORKER_WORK_MAP.md`, and PRs #8927, #8937, #8968, #8969, #9016, and
[#9099](https://github.com/Unjuno/agent-interface/pull/9099), including the
seven-run Xvfb report/raw chain referenced there.

**Deliver:** `issue-5-target-binding-crosswalk-20261019-r01.md`. Reconcile the
agenda/work-map wording with #9099's private-Xvfb standard-caller result; keep
the synthetic target's independent property effect distinct from product-app
semantics, native desktop/XWayland, atomic check/use, and task completion. State
the exact prerequisites for one supported-application target and an
independent app-state oracle. Mark owner and eligible allocation `unknown`
unless freshly verified. Do not rerun #9099 or start live input.

**Exit:** an evidence-backed note separates the Fake X construction checks from
the limited private-Xvfb caller result and states all remaining gates. Do not
repeat the already-merged #9099 result. Issue #5 stays open unless a separate
evidence-backed disposition is proposed and reviewed.

## Packet C — #59 MAP01 evidence custody and A07 reconstruction

**Question:** Can the open #8702 A07 cancellation/key-up reconstruction be
independently matched to the tracked A07 packet preserved by #9148, and which
raw artifacts remain unavailable?

**Read:** Issue [#59](https://github.com/Unjuno/agent-interface/issues/59),
open PR [#8702](https://github.com/Unjuno/agent-interface/pull/8702) at its
current exact head, preservation PR [#9148](https://github.com/Unjuno/agent-interface/pull/9148),
`docs/ideas/map01-live-guard-evidence-family.md`, the MAP01 row in
`docs/WORKER_WORK_MAP.md`, and the author-attested custody material already
linked from those sources.

**Deliver:** `issue-59-a07-custody-audit-20261019-r01.md`. Compare available
path/size/hash evidence and report exact matches, missing artifacts, and whether
the terminal X11 cleanup classification follows from accessible source. Keep
`formal_pass=false`, the original HOLD/STOP, absence of useful scorer/task
effect, and unknown physical verification explicit. Treat an inaccessible raw
bundle as “not available in inspected sources,” not globally lost.

**Exit:** independent hash/custody comparison or a precise missing-artifact
inventory. No A07 rerun, allocation, Issue/PR closure, or claim of physical
release/task success. The still-open #59 remains separate from #57 efficiency.

## Integration and ordering

The three packets can be researched concurrently because they use separate
families and output paths. Shared indexes and the family records are updated
serially after the evidence packets are checked. A packet may reveal a concrete
implementation task; that task gets its own branch/output scope and must
re-check current ownership and prerequisites before execution. These packets
do not authorize closing the parent Issues or changing active experiment state.
