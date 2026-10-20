# Repository cleanup plan

## Current state after PR #9241 — 2026-10-20 07:26 UTC

Main is `41f1dc570a2affddece6ee894ed42d216b21a993`. The [r109 membership recheck](maintenance/repository-inventory-recheck-20261020-r109.md) confirms 1,672 open Issues and 468 open PRs, with both ID sets unchanged from r108. PRs #9240 and #9241 were created and merged between the snapshots; neither remains open. The latest complete row-level metadata remains [r108](maintenance/repository-inventory-20261020-r108.md); r109 refreshes membership only. PR #9241 added the #17 fault-layer evidence crosswalk; #17 remains open and no allocation or Issue state change occurred.

### Next organization wave

1. Use r109 as the latest membership check and r108 as the latest full metadata baseline; refresh exact live records before another remote state-changing batch.
2. Source-map the uncovered #17 stdout-delivery and image/receipt-serialization paths to the standard caller, then select one composed check that distinguishes them.
3. Continue one disjoint family at a time, preserving ideas, first outcomes, raw evidence, scope limits, dependencies, and the next finite decision.
4. Review candidate PRs by exact head/base and complete diff. Integrate verified useful records on current main; close predecessors only after successor content and evidence custody are confirmed.
5. Retain branches/worktrees/artifacts with unknown ownership until owner, process, dependency, and recovery path are known.
6. Keep shared maps and indexes current while allowing workers to use separate family/output paths.

Repository-wide cleanup remains incomplete until active ideas and artifacts have traceable dispositions and workers can start independent tasks from the map.

## Current state after PR #9238 — 2026-10-20 06:54 UTC

Main is `5ce0f2b67d3dafcde70cc84b9832d5f841475210` after PR #9238. The latest complete paginated membership read is [r108](maintenance/repository-inventory-20261020-r108.md): 1,672 open Issues and 468 open PRs at this SHA, bracketed by matching GraphQL counts. Relative to r107, #8861 left the open PR set after its construction package was integrated by #9238; #9238 was created and merged between captures and appears in neither open set. Issue membership is unchanged. The [r108 delta](maintenance/repository-inventory-20261020-r108-delta.json) records this transition.

Current-main [PR #9234](https://github.com/Unjuno/agent-interface/pull/9234) preserves original #8848's A12 soft-ammo feedback packet; seven CRLF-derived checksums are corrected against exact Git blobs, with frozen source/raw/audit unchanged. The consumed WSLc test was not rerun. Current-main [PR #9236](https://github.com/Unjuno/agent-interface/pull/9236) preserves #8840's A03 first `HOLD_UNCERTAIN`, repairs the generated analysis index, and organizes the #31/#8636 family. The 2,231-file archive and 17-member checksum manifest were independently verified; the candidate and auditor were not rerun. Current-main successor [PR #9238](https://github.com/Unjuno/agent-interface/pull/9238) merged at `5ce0f2b67d3dafcde70cc84b9832d5f841475210` and carries #8861’s oracle-boundary construction patch; its guarded local verifier passed four focused and 13 applicable A04 tests in normal and optimized Python against a temporary pinned copy. Replay-gate, analysis-index, public-navigation, research-workspace-index and three method-contract checks passed; one additional method-contract check remained in checkout when merged, while its same suite passed locally. No candidate/auditor or WSLc allocation was rerun; A04 remains `HOLD_UNCERTAIN`. Original #8848, #8840 and #8861 were closed as superseded; Issues #59, #31, and #8636 remain open because these records do not establish live task effect or the relative-view feature hypothesis.

The prior batches integrated A08 evidence through #9228 and Win32 release-state tests through #9230. Parent Issues #17/#57/#59 remain open. No WSLc allocation was used, and worktree/raw-data custody remains incomplete. Unknown-owned artifacts remain retained.

### Next organization wave

1. Keep r108 as the latest full membership baseline; refresh it before another remote state-changing batch.
2. **Completed bounded family disposition:** [Issue #17 fault-layer crosswalk r02](maintenance/issue-family-disposition-input-safety-20261020-r02.md) separates journal stalls, owner-blocked Xlib with a responsive server, full-server-stop failure, and post-resume cleanup. It keeps #17 open and retains each positive, negative, and unknown outcome at its actual scope. Next, source-map the uncovered stdout-delivery and image/receipt-serialization paths to the standard caller before selecting a composed check.
3. Continue one disjoint family at a time, preserving ideas, first outcomes, raw evidence, scope limits, dependencies, and the next finite decision.
4. Review candidate PRs by exact head/base and complete diff. Integrate verified useful records on current main; close predecessors only after successor content and evidence custody are confirmed.
5. Retain branches/worktrees/artifacts with unknown ownership until owner, process, dependency, and recovery path are known.
6. Keep shared maps and indexes current while allowing workers to use separate family/output paths.

Repository-wide cleanup remains incomplete until active ideas and artifacts have traceable dispositions and workers can start independent tasks from the map.

## Previous state after PR #9230 — 2026-10-20 06:17 UTC

Current main is `018d490c547fa379f5034e4cf14d8893ebf58d48`. The latest complete paginated membership read is [r104](maintenance/repository-inventory-20261020-r104.md): 1,672 open Issues and 472 open PRs, with matching GraphQL counts and stable main SHA. Relative to r103, Issues are unchanged and PR #9006 left the open set. Current-main [PR #9230](https://github.com/Unjuno/agent-interface/pull/9230) integrated five test-only Win32 release-state cases; focused Windows tests passed 19/19, and native-mcp, native-win32, builds, CLI, and replay checks passed. It changes no production behavior and does not prove physical input release. Original PR #9006 is closed as superseded; no parent Issue was closed. The [r104 delta](maintenance/repository-inventory-20261020-r104-delta.json) records the transition.

The previous batch integrated the A08 focused-observation package through #9228 and closed identical PRs #8807/#8808; Issue #1998 remains open. No WSLc allocation was used. Broader worktree/raw-data custody remains incomplete; unknown-owned artifacts are retained. Issues #17, #57, and #59 remain open.

### Next organization wave

1. Keep r104 as the latest paginated membership baseline; refresh it before another remote state-changing batch.
2. Continue one disjoint research family at a time. Preserve hypotheses, first outcomes, raw evidence, limits, dependencies, and one finite next decision.
3. Review PRs against exact current head/base. Integrate useful work at current main; close superseded PRs only after verifying evidence custody and the canonical successor.
4. Reconcile branches/worktrees/artifacts only after checking owner, process, dependencies, and recovery path. Unknown custody remains retained.
5. Keep shared navigation accurate and concise; independent families use separate outputs, while shared indexes are integrated serially.

Repository-wide cleanup remains incomplete until active ideas and artifacts have traceable dispositions and workers can start independently from the map.

## Previous state after PR #9228 — 2026-10-20 06:11 UTC

Current main is `a5a45a9375f240ccc19e4b5268947b32fd830e4a`. The latest complete paginated membership read is [r103](maintenance/repository-inventory-20261020-r103.md): 1,672 open Issues and 473 open PRs, with matching GraphQL counts and stable main SHA. Relative to r101, the open Issue set is unchanged and PRs #8807/#8808 left the open set. PR #9228 integrated their identical 23-file A08 package at current main; the formal frozen result was preserved unchanged, and only its nine-test construction suite was rerun locally. The [r103 delta](maintenance/repository-inventory-20261020-r103-delta.json) records the transition. Issue #1998 stays open for its distinct unresolved GUI, model-utility, latency, and product-transfer questions.

This is one verified duplicate-PR disposition, not a repository-wide cleanup. The r103 inventory is metadata, not semantic triage. Custody work remains incomplete; retain unknown branches, worktrees, ignored data, and generated artifacts. Issues #17, #57, and #59 remain open. No WSLc allocation was used or inferred.

### Next organization wave

1. Keep r103 as the latest paginated membership baseline; refresh before any later state-changing batch.
2. Continue with one disjoint family at a time, preserving distinct hypotheses, first outcomes, raw links, evidence limits, dependencies, and one finite next decision.
3. Review PRs by exact current head/base and complete diff. Merge useful verified records; for duplicates, verify identical content and preserved evidence before closing only after the canonical result lands.
4. Reconcile branches/worktrees/artifacts only after owner, process, dependency, and recovery-path checks. Unknown custody remains retained.
5. Keep navigation indexes concise and collision boundaries explicit so workers can proceed independently; serialize only shared-index edits.

The wave completes when its selected items have evidence-backed dispositions and a worker can start from the map. Repository-wide cleanup remains incomplete until active items, ideas, dependencies, and artifacts all have traceable dispositions.

## Previous state after PR #9226 — 2026-10-20 06:02 UTC

Current main is `000d4aff06e2062e3fc19077e0f88b8334ffa080` after PR #9226. The latest complete row-level read is [recheck r102](maintenance/repository-inventory-20261020-r102.md): 1,672 open Issues and 475 open PRs, bracketed by GraphQL at the same main SHA. The refreshed Issue and PR exports are byte-identical to r101 and its immutable CSVs are reused; PR #9226 opened and merged between captures and is absent from both open snapshots. See the [r102 delta record](maintenance/repository-inventory-20261020-r102-delta.json). Counts are not semantic triage; re-fetch the exact live record before changing state.

PR #9225 added the bounded post-resume release-only retry; PR #9226 added monotonic owner-liveness snapshot timing and preserved five standard-caller Xvfb blocked-owner trials. In those trials the independent synthetic task oracle passed and readbacks found both keys up, while the caller retained `UNKNOWN`, denied replay, and the terminal snapshot lacked capture time. PR #9226 now adds the timestamp and a live Xvfb ordering assertion. These results still do not prove release during a full X-server stop, MAP01 completion, broad reliability, or integrated efficiency; Issues #17, #57, and #59 remain open research questions. The broader branch/worktree/raw-data custody audit remains incomplete; no workspace deletion is authorized by a count or a clean Git status.

### Next organization wave

1. **Done for the previous baseline:** r102 rechecked the full paginated Issue/PR metadata and is bracketed by GraphQL at the same main SHA; exports match r101 byte-for-byte. It is retained as history; r103 is now the latest membership baseline.
2. Process one disjoint research-family batch at a time. For each Issue, preserve its distinct hypothesis, strongest comparator, actual first result and raw link, scope limits, dependency/owner, and one finite next decision in its canonical family record. Keep unclassified items in a visible queue.
3. Separately triage PRs by exact live head/base, diff, checks, author/owner, dependencies, and unique evidence custody. Merge validated useful work; repair or transfer unique work before closing duplicates; retain unresolved ownership and unique data.
4. Reconcile local branches, worktrees, ignored data, and generated artifacts only after exact owner/process/dependency checks and a verified recovery path. Unknown custody remains retained and labeled.
5. Keep the worker map as a navigation surface with disjoint paths and collision boundaries. Serialize edits to shared indexes; do not serialize independent research families.

The wave is complete when every item in its selected slice has a traceable evidence-backed disposition and a worker can start the next independent task from its map entry. Repository-wide cleanup is complete only when all active items and artifacts have dispositions, unresolved ideas and ownership are visible, and no deletion or closure is being used to make counts look clean.

## Current execution baseline — 2026-10-20 05:26 UTC

At main `282a05b02d8d48053c88bcdb08ace54694068a6a`, the fresh paginated inventory is [r100](maintenance/repository-inventory-20261020-r100.md): 1,672 open Issues and 476 open PRs. It supersedes r99 for membership. Since r98, #8574 and #8843 left the open sets. Both transitions are reconciled: #8574's scoped T0 question is recorded `NO_INCREMENTAL_VALUE_SCOPED`, preserved by merged [PR #9217](https://github.com/Unjuno/agent-interface/pull/9217), and closed with broader transfer left deferred; #8843 was a stale-base duplicate superseded by merged [PR #9218](https://github.com/Unjuno/agent-interface/pull/9218), which preserves all 19 package blobs, repairs seven manifest entries, and retains the construction-only scope. After r99, #8832 was closed as duplicate of #9217 with its frozen data retained. PR #9224 is the current documentation/inventory refresh. None of these closures resolves the broader live-control Issue #59.

At the time of the r100 update, exact reads found #8848 Draft/open at `6f95e7dc6d37e1dd97f5d47882796d94902478c7` and #8840 open at `7d9aba384b0d799119f330c9c763e60703ecc320`; both had stale bases. #8832 was already closed as superseded by merged #9217. The #8848 manifest follow-up was completed by #9234 (r03); the #8840 checksum/index repair was completed by #9236 (r04). Their saved negative/uncertain results remain intact.

This is a membership and routing refresh, not proof that the repository is semantically clean. Historical inventories and experiment records remain immutable; do not delete them to reduce noise. Continue family-by-family triage and only close an Issue when its distinct question, material outcomes, evidence limits, dependencies, disposition, successor (if any), and reopen condition are recorded.

This plan makes the repository easier to work in with many independent workers while preserving research questions, first outcomes, evidence, ownership, and dependencies. It does not define success as zero open Issues or PRs.

## Execution refresh — 2026-10-20

The compiled-caller fix [PR #9213](https://github.com/Unjuno/agent-interface/pull/9213) merged at `5bdef852869d8a3a1c2de792221fadd0db199586`, fixing a post-merge `FakeBridge.scope` compatibility regression from #9212; native-MCP and X11 integration checks passed and raw failure/follow-up logs remain with the compiled-caller packet. Documentation refresh [PR #9214](https://github.com/Unjuno/agent-interface/pull/9214) is now current main `d123634bcc11db30baf3ec73f90429cea6d0b135`; it made no Issue/PR state changes, so full paginated inventory [r98](maintenance/repository-inventory-20261020-r98.md), captured at the preceding `5bdef…` commit, remains the current membership set: 1,673 open Issues and 477 open PRs, with GraphQL agreement. Issue membership matches r97; the open PR set lost #8772 and #8842. This still is not semantic triage or proof of custody. Three read-only cleanup audits identified finite independent family and PR review packets in the [parallel worker map](maintenance/parallel-worker-packets-20261020-r01.md). The local custody audit found 29 registered worktrees (8 dirty), 133 branches, and 212 immediate `work` directories; do not infer stale ownership or delete/reset/prune any of them from those counts.

The earlier count-only checkpoint was at `87dfb33d94f3a8bbe12fbf3ab5bc7f0433c8d8c5`; it returned 1,673 open Issues and 479 open PRs but did not refresh the inventory. A full paginated refresh is now preserved as [r97](maintenance/repository-inventory-20261019-r97.md) at main `4ef4169b28952ff9b546cb1ab19aed74bb5efce0`. The count-only checkpoint is superseded by r97. No remote Issue or PR state was changed for inventory capture.

At that earlier checkpoint, a count-only read at main `e4246c87e5f3e6f63acb7f424ee7f557f2bfb5f1` returned 1,673 open Issues and 477 open PRs but was not a row-level refresh. It has since been superseded by r98. Re-fetch exact items and ownership before each disposition.

The user's organizing objective is to make the repository safe for many workers to contribute independently while keeping ideas available for future research. A catalog entry is a way to preserve and connect an idea, not a reason to close its Issue. Close an Issue only after its distinct question, evidence and limits, dependencies, disposition, successor (if any), and reopen condition are recorded. Keep unresolved computer-control goals, active assignments, integration work, and evidence-custody gaps open. Review and integrate PRs as a separate stream; never infer a PR's disposition from its Issue or from an inventory row.

### Previous read — 2026-10-20 05:05 UTC

The current `main` is `e18f0fc7d1fb075eff074aa5d5ceb3491016e397` (PR #9219). A live GraphQL count-only read returned 1,672 open Issues and 477 open PRs. This is newer than the fully paginated r98 snapshot, but it is **not** a current membership export; do not infer which IDs changed or treat the backlog as semantically classified. Issue #8574 is confirmed closed after its scoped result was preserved through #9217. Issues #17, #57, #59, and #7924 remain open; #17/#57/#59 retain unresolved research goals, and #7924 remains STOP/HOLD pending an owner/release and unused-allocation evidence.

PR #9220 is open against the exact current `main` SHA above. Its previous head `05257866823ba373a6a993707ce2cc4fba14d276` failed X11 integration run `39372751034` on one assertion: when the X server stops, caller state correctly reports `owner_client_disconnect=UNKNOWN` and refuses to start release absent disconnect confirmation (`owner_release_attempt=not_attempted`, reason `owner_disconnect_not_confirmed`). Cleanup remains `UNKNOWN`, the held-key obligation is retained, `task_success=null`, and replay is denied. The test expected `unknown` for the release attempt, so the assertion was corrected to match the fail-closed contract in head `c7d2a9e193612d181156b822849d7bfbce125310`. The relevant local Python suite passed 36 tests with the private-Xvfb test skipped on Windows; `py_compile` and `git diff --check` passed. Two new-head review/audit checks are queued. Keep #9220 `needs-checks`, not merge-ready, until the exact-head Linux X11 integration passes. This result is bounded to a stopped private X server and does not certify physical release or general outage recovery.

The 2026-10-20 review-gate scan remains a text-screen of 39 Draft PR bodies, not a verified set of active policy violations. Current operating entry points (`CURRENT_GOAL.md`, `WORKER_QUICKSTART.md`, and `WORKER_WORK_MAP.md`) already state that no reviewer-count quota is added; actual branch protection and project rules remain the only repository-level enforced gates observed in the latest audit (none were configured). Treat old PR bodies and historical experiment packets as source history: review any matching active PR individually, preserve its real scientific acceptance conditions, and remove an invented fixed seat/count rule from an active instruction only after checking its scope and current evidence.

This refresh changes no GitHub Issue/PR state and does not claim a clean repository. The next cleanup batch remains item-level: preserve each idea and its result first, then decide whether that specific Issue is actionable, blocked, catalogued/deferred, completed in scope, superseded, or out of scope. In parallel, PRs receive exact-head diff/check/custody review. Unknown worktree or raw-data ownership stays on HOLD. A smaller count is never the target; traceable ideas, clear ownership/collision boundaries, and independent bounded worker packets are.

### Post-merge refresh — 2026-10-20 05:13 UTC

Main is now `de852bf3b65ad5b8debac3b7e0138bcf843e7313` after PR #9220; PR #9221 had already merged the cleanup-plan refresh at `3daed8acf60b7cd0eac06fecfefb9ec9778c08c8`. A live GraphQL count-only read reports 1,672 open Issues and 476 open PRs. It is not a fresh paginated membership export; r98 remains the most recent full set, and the count changes do not establish semantic disposition.

PR #9220 merged after its test-only expectation was corrected and rebased onto the current main. On exact head `4262d979a451266dae79e595aa68dc7ef400331c`, all reported checks passed, including private-Xvfb X11 integration run [39373461786](https://github.com/Unjuno/agent-interface/actions/runs/39373461786). The downloaded raw result and hash are now preserved in the [server-stop r01 packet](../research/integration/standard_caller_xvfb_server_stop_20261020/r01/README.md). Cancel returned within 0.409 s, but key `a` remained down at the 8.5 s post-resume horizon; the synthetic task oracle failed, runtime task_success stayed null, release/cleanup stayed UNKNOWN, and replay remained denied. The owner-retirement and terminal-liveness receipts conflict and remain a follow-up question. This is a retained failure/counterexample, not resolution of Issue #17 or proof of general release/recovery.

The 05:05 checkpoint above is historical and its `needs-checks` status for #9220 is superseded by this result. The plan PR and test PR are integrated; repository-wide Issue/PR semantic classification and local worktree custody are still incomplete. Keep actionable/research/blocked items open and continue with disjoint family packets; do not close more items solely to reduce counts.

### First confirmed reviewer-quorum disposition — 2026-10-20 05:18 UTC

At main `eca99d0da17938e71707e4530d80e15ed7ca1d35`, the live Draft body of [PR #7283](https://github.com/Unjuno/agent-interface/pull/7283) explicitly required two nonauthor approvals, named reviewer seats, and a committee epoch. Its body now prominently withdraws that fixed-count/seat requirement: workers must not wait for a reviewer count or recruit a named person. The original proposal metadata remains below the notice as historical provenance, not an active gate. The actual technical acceptance conditions remain: validate the exact source/evidence, refresh composition against current `main`, and satisfy the applicable platform/owner/cancellation/sole-sender safety checks.

This wording change did not alter source code, experiments, Issue state, or PR state. #7283 remains Draft/open and is not merge-ready: its head is `92a610b30507e9ac0c159ca18ac8a8502c8d5b1c`, its base `6dee2bff223c7e9643949d2a8ef3acf7e9b007da` is old, and GitHub reports `DIRTY`. The related current-main rescue #8368 is also Draft/open and `DIRTY` against base `ea2af10f1111ba614311e354dfecde1bbf653981`; it needs exact-diff and current-base validation separately. The r01 scan's 39 body matches remain a historical candidate set, not 39 confirmed operative gates; the remaining candidates require individual live review. The count-only baseline at this main is 1,672 open Issues and 476 open PRs; it does not replace the last full membership export or semantic triage.

## Computer-control checkpoint — 2026-10-20


After #9213, a live refresh still shows [Issue #17](https://github.com/Unjuno/agent-interface/issues/17) and [Issue #57](https://github.com/Unjuno/agent-interface/issues/57) open. PRs #9212/#9213 add the standard-MCP compiled caller and repair its ordinary-bridge compatibility; Fake X and Xvfb integration checks do not establish independent task success, bounded physical release/recovery, or matched efficiency. Keep both Issues open until their separate exit conditions are evidenced.

## Prior full inventory snapshot r97 — 2026-10-19 16:00 UTC

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
## Historical live PR spot review of #9006 (before PR #9230)

PR [#9006](https://github.com/Unjuno/agent-interface/pull/9006) was first re-read at head `655a5bcdf6026650044e0157343d4e0de268a548`. Its old-head native checks failed, including a real-fixture `release_unverified` result when `GetAsyncKeyState == 0`. The five pure test cases were reapplied to current main and validated by [PR #9230](https://github.com/Unjuno/agent-interface/pull/9230): 19 focused Windows tests passed, and exact-head native-mcp, native-win32, build, CLI, and replay checks passed. #9230 changed tests only; the zero/unknown state remains fail-closed. **Disposition: #9006 superseded and closed after transfer; no physical-release claim.** This spot review covers only this PR, not the remaining backlog.
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

**Review-quorum cleanup (2026-10-20):** A read-only GitHub CLI scan against main `b38e49f8cf5cef3a30f33e945bf71feca838eae0` returned 477 open PRs. Thirty-nine Draft bodies matched explicit markers such as `required_nonauthor_content_votes`, a threshold of two, or a two-nonauthor quorum; the candidate numbers are listed in [review-gate scan r01](maintenance/review-gate-candidate-scan-20261020-r01.md). This is a body-text screen, not a completed review of those 39 PRs or proof that every match is an applicable gate. A live read of `main` branch protection returned “Branch not protected”; the repository rulesets endpoint returned an empty list. Therefore a PR body or Issue-local protocol is not by itself a repository-wide worker/merge quota. Preserve each proposal's actual scientific acceptance tests, required platform/ownership checks, and meaningful independent audit evidence; remove fixed reviewer-seat/count requirements from active operating instructions unless they are an actual GitHub protection or an explicitly current, user-authorized task acceptance condition. Treat the 39 matches as a finite PR triage batch, beginning with the computer-control #59/#57 items, and revise each exact live body only after checking its head, dependency, and retained evidence. Do not change PR state or delete branches as part of this scan.

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
