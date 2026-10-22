# PR #8678 MAP01 A01/A02 evidence custody review (2026-10-19)

PR [#8678](https://github.com/Unjuno/agent-interface/pull/8678), exact head `7551424026375469f609754140250f89bf09cad4`, contains 29 added files across two distinct artifacts: an A01 prelaunch STOP and the first A02 live MAP01 threat-guard attempt. All 29 paths are absent from current main `a6741224fad3cfd29de7bd4becac9cc207490242`. They contain no production-source changes. The frozen source commit `5f1761cec6b6b8cb4513aef6dbe0429d35569e97` is reachable from current main.

## Result and limits

A01 stopped before freeze, game startup, or model call because the host runner addressed a WAD path visible only inside the VM. Its `PRELAUNCH_STOP.json` records zero model calls and no game/input action.

A02 was a one-shot run in a dedicated OrbStack arm64 VM with four completed low-effort model turns. Health changed 97→91→85 and ammo 48→41, but the preregistered hard-health floors were not crossed. The run stopped after cover cancellation raised `ValueError: up_batch requires the active input lease`. Although keymap snapshots reported empty keys, the controller marked the terminal failed and cleanup incomplete; the retained audit reports `formal_pass: false`. The score was one kill, no death, and no MAP01 exit. The consumed run was not retried. This does not establish physical input release, hard-guard invalidation, stale-answer rejection, bounded recovery, or task success.

The tracked PR diff includes the frozen result, independent audit, source/fixture identity data, and selected protocol/input/scorer traces. Its `SHA256SUMS.json` inventories 976 files in the ignored output path `results-local/doom/map01-v39-live-threat-guard-a02-20261009/`; the PR body says full raw images and transport artifacts remain there. That directory was not present at the corresponding path in the current checkout or any of the 15 registered worktree roots checked on 2026-10-19. This is a scoped absence check, not proof that the data is unavailable elsewhere. Therefore this transfer preserves the complete Git-tracked PR diff, but does not claim custody of the 976-file ignored output bundle.

## Separation and disposition

PR [#8701](https://github.com/Unjuno/agent-interface/pull/8701) is a separate A03–A07 allocation series with 41 distinct research paths plus a `CURRENT_GOAL.md` change; it is not a duplicate of A01/A02. Do not merge or close the two packets as one result. Issue #59 remains open, and none of these attempts establishes its integrated live-control gate.

This review does not rerun the candidate, audit, tests, model, game, or allocation. Preserve the 29 tracked files exactly. Only after main-tree readback can #8678 be considered superseded at the Git-diff level. The external ignored output remains a documented custody gap even if its branch is later retired. See the [MAP01 evidence-family index](../ideas/map01-live-guard-evidence-family.md) for the ongoing per-allocation boundaries.
