# Targeted PR disposition audit: #10144 — 2026-11-23

## Decision

**RETAIN OPEN AS DRAFT; do not merge this head or close it as obsolete.** The PR is a research artifact set with potentially unique records, and its author explicitly says the lifecycle prototype is not ready for live use and asks to keep the PR Draft. The stated live-use blockers are still material to the project goal. Preserve custody while separating reusable evidence from implementation that would need a current-main rebase and fresh qualification.

## Current remote evidence

- PR: [#10144](https://github.com/Unjuno/agent-interface/pull/10144), open and Draft, last updated 2026-11-02 16:21 UTC.
- Head: `a17b7fe8d31cedecc5f70575770f5cc3c4f7fe7f`; last commit 2026-11-03T01:20:41+09:00.
- Declared base: `22362cb7b31ef2329d718cd636eaece4d50c0137`; current main at audit: `3a705de2bef0b0b5ef1a569cf63a58664b732c01`.
- GitHub compare reports the PR branch diverged from current main, 44 commits ahead, 524 behind, 174 files, no merge base. All 174 PR paths are absent from current main; change size is 13,629 added lines and zero deletions.
- Only listed status check is replay-gate PASS from Nov 2. No current-main test result, required review decision, or merge readiness is present (`mergeable`/`mergeStateStatus` UNKNOWN in the PR view).
- The author reports 100/100 local tests normal and `-O` on Nov 3 with SSD-backed temp, while explicitly preserving an earlier HDD-backed failure (6 failures + 4 errors; 488.706 s). This is historical prototype evidence, not a current-main qualification.

## Author-declared live-use gaps

The PR body requires parent-independent custody/restart reconciliation, bounded synchronous process creation/WSLc/fsync/cleanup/audit, complete descendant retirement under interruption/concurrency, independently authenticated release, an independent Calc scorer, preserved/audited artifacts, and matched task/effect/release/recovery trials with all attempts and lifecycle accounting. It also says the scorer/release fields are injected/trusted and the time budgets remain advisory.

Later current-main evidence has advanced adjacent contracts: the #57 Calc composition crosswalk and synthetic ProspectiveRun R01-R06 now show durable synthetic joins and full offline projection. They do not close the PR's real WSLc custody, independent scoring, live provider, task-effect, or matched-efficiency gaps. See [Calc crosswalk](issue57-calc-evidence-bridge-audit-20261123.md) and [R06](../../research/integration/issue57_v3_durable_appserver_full_trace_r06_20261123/RESULT.md).

## Disposition rationale and next action

Do not merge solely to make the PR queue shorter: that would promote 174 unreviewed files and a prototype explicitly marked not ready. Do not close it: all PR paths are unique to this branch and include 13,629 lines of experiment/code artifacts whose custody has not been reconciled elsewhere. The next useful action is a current-main rebase/slice review: map the PR's evidence artifacts and implementation files to the newer R01-R06 Calc ledger; verify artifact manifests; retain useful historical evidence; then port only still-needed mechanics behind current-main contracts and rerun targeted tests. A separate explicitly scoped change should supersede or close #10144 only after that review establishes that its unique evidence is preserved and its implementation is either integrated or intentionally rejected.

This audit does not dispatch WSLc, Docker, GUI, provider/model, or Calc actions.
