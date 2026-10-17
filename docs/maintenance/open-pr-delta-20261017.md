# Open PR delta from the 2026-10-16 r3 inventory

This snapshot compares the live GitHub open-PR set on 2026-10-17 with
[`open-prs-20261016-r3.csv`](open-prs-20261016-r3.csv). The set grew from 517 to
521: seven PRs entered the open set and three left it. This is a change log for
that delta, not a content review of all 521 PRs. The complete metadata read is
retained in [`open-prs-20261017-r4.csv`](open-prs-20261017-r4.csv), with scope
and limits in [the inventory note](open-pr-inventory-20261017.md).

## Newly open

| PR | Current role and evidence | Next disposition |
|---|---|---|
| [#9005](https://github.com/Unjuno/agent-interface/pull/9005) | Model-interaction/evaluation family agenda plus an outcome row for #9004. Exact head `63d4d22f` records #9004's scoped T0 result from #9009; all three reported checks pass and GitHub reports `CLEAN`, with no review decision. Readback of the exact diff shows the #9004 section in `model-coupling-and-evaluation-agenda.md` and its `IDEAS_AND_OUTCOMES.md` row; the #9004 note is not one of the 49 entries in #9012's `open-issue-citation-audit-20261017.md`. #9012 separately carries the issue-specific `agreement-conditioned-continuation.md` result note and index row. | Keep #9005 as family navigation and #9012's issue note as the detailed result record. At integration, link the family entry to the canonical issue note and avoid maintaining two copies of the numeric outcome; retain the compact `IDEAS_AND_OUTCOMES` index row. |
| [#9006](https://github.com/Unjuno/agent-interface/pull/9006) | Draft, test-only Win32 release-custody port; PR diff adds tests only. Cross-platform build/CLI and replay checks pass. The native-mcp workflow reports four unrelated suite failures; native-win32 fails the unchanged integration assertion because release verification returns `release_unverified` rather than `completed`. | Keep draft pending a decision on the release-verification contract and suite failures. Do not resolve by weakening the expected release guarantee. |
| [#9007](https://github.com/Unjuno/agent-interface/pull/9007) | Preserves two CPU-only synthetic #8914 allocations; each independent audit failed at sentinel reconstruction before scientific gates. All reported checks pass. | Preserve as an audit-method failure record; the two allocation outcomes are not a scientific comparison. |
| [#9008](https://github.com/Unjuno/agent-interface/pull/9008) | V39 paired-observation watermark repair with a retained-trace regression and independent audit. The prior Codex P2 on unconditional watermark advancement was addressed in exact head `27a54639`: only full `observation` now advances the watermark, and a new retained-trace regression proves typed-only soft evidence waits for full-row reconciliation. Five focused tests (the current-main replay regression plus frozen v3 tests) pass locally. A broader discovery also executes three preserved v1/v2 assertions that encode superseded assumptions and fail within their historical snapshots; the package records their correction in `DEVIATION.md`. | Keep the fix candidate open for exact-head CI and non-author review; current local tests and prior checks do not establish current-main integration. |
| [#9009](https://github.com/Unjuno/agent-interface/pull/9009) | CPU-only synthetic #9004 T0: 40 rows, independent reconstruction, 5/5 mutation controls; the preregistered trace family showed no incremental agreement value. Three reported checks pass. | Preserve the scoped negative result; do not promote it to a live-model or product claim. |
| [#9011](https://github.com/Unjuno/agent-interface/pull/9011) | Native MCP guarded-recovery forwarding and guarded-package source-closure repair. Static inspection of exact head `62b3d163` found that the new recovery tool is added to the public relay allowlist while legacy-relay parity explicitly excludes it; preregistration source checks now raise `RuntimeError` rather than relying on removable assertions; guarded-package implementation files are enumerated from the package directory while excluding tests. No correctness issue was found in this source review. All reported checks pass, including native-mcp, X11 integration, audit, and replay-gate. | Keep as an implementation candidate pending a recorded review decision; these checks and this source review do not establish current-main integration. |
| [#9012](https://github.com/Unjuno/agent-interface/pull/9012) | Consolidated idea ledger, fresh Issue/PR inventory snapshots, and branch-cleanup receipts. Current head `c3120918` includes the correction distinguishing #9005's family agenda from #9012's detailed #9004 result note. GitHub reports `UNSTABLE`, no review decision; replay-gate, public-navigation, and research-workspace-index pass, while analysis-index and three method-contract checks are pending. | Keep separate from implementation/evidence PRs. Recheck the exact head's pending checks and review state before integration; branch retirement remains contingent on archive integration and exact-tip/reference readback. |

## No longer open

| PR | Current state and dependency | Cleanup implication |
|---|---|---|
| [#8714](https://github.com/Unjuno/agent-interface/pull/8714) | Closed unmerged. Its branch is still the base of open [#8720](https://github.com/Unjuno/agent-interface/pull/8720). | Retain the base branch while #8720 is open; do not count the closed PR alone as evidence that the branch is redundant. |
| [#8867](https://github.com/Unjuno/agent-interface/pull/8867) | Closed unmerged; its measurement changes and source history are reconciled in [`consolidation-status-20261016.md`](consolidation-status-20261016.md). | Keep its recorded successor/custody path distinct from direct-merge accounting. |
| [#8874](https://github.com/Unjuno/agent-interface/pull/8874) | Closed unmerged; original source and the referenced missing log are recorded in [`consolidation-status-20261016.md`](consolidation-status-20261016.md). | Treat closure as evidence-preservation handling, not as a successful experiment or direct merge. |

All states above were read from GitHub on 2026-10-17. The seven PRs are a
selected delta, not a determination that the remaining open PRs are redundant,
integrated, or fully classified.
