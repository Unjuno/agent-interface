# Archival qualification: #5082 / source PR #5163

This is a preservation-only copy of the eleven files published in [source PR #5163](https://github.com/Unjuno/agent-interface/pull/5163) at exact head `51ac8a5eef125cdad0a1e6445e355c51a0dd1d3d`. It retains construction source, tests, inert input, plan, and freeze metadata. It is not a formal publication result, a new freeze, a resource assignment, or an authorization to run the retained programs.

## Exact-byte provenance

All eleven original files retain their original Git blob IDs, modes, and bytes from source directory tree `b6d82c52d445153ea83a6c490fe1b727fc21c055`. All ten entries in [FREEZE.json](FREEZE.json) match their SHA-256, Git blob, and byte-size declarations. The decoded inert seed input also matches its declared 15,279-byte length, SHA-256, and original Git blob `45b80150dac503f4eb6f3cb5d82f9afa2c587107`. The nested `.gitattributes` remains unchanged; original CRLF bytes in the plan and freeze are preserved.

This qualification is additive commentary, outside the frozen ten-entry source manifest. The freeze's `intake_main` and `source_publication_main` remain the historical `5670372e20065d3d8286105ed4ea9615952b116f`. Copying these files onto a newer main does not refresh their experimental freeze or satisfy an exact-current-main execution gate.

## Construction evidence and its limits

- The [September 28 exact-head verification](https://github.com/Unjuno/agent-interface/issues/5082#issuecomment-5862894080) reports 17/17 host construction tests, compileall, frozen identity checks, and a static Docker Desktop preflight.
- The later [September 30 construction receipt](https://github.com/Unjuno/agent-interface/pull/5163#issuecomment-5906804960) reports **17/17 tests passed in one disposable pinned Docker Desktop construction container**, exit 0, in 0.032 seconds. This supersedes a blanket reading of earlier “zero container runs” status.
- That receipt names `desktop-linux`, image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, `linux/amd64`, pull-never/network-none, read-only root/source, 1 CPU, 512 MiB RAM, 64 PIDs, dropped capabilities, no-new-privileges, and bounded temporary storage. These are the construction invocation's settings, distinct from the unexecuted formal allocation's frozen resource settings.
- The receipt reports a clean source worktree, no persistent output, and automatic container removal. It explicitly did **not** run the frozen 4,096-publication experiment, exercise filesystem publication behavior, or invoke the independent formal raw auditor.
- [GitHub Actions run 36374516316](https://github.com/Unjuno/agent-interface/actions/runs/36374516316) is recorded as successful for the exact source head. It is a repository replay-gate workflow, not the formal runner/auditor allocation.

These historical test outcomes are attributed to the linked records. The original eleven-file bundle contains no standalone September 30 command transcript, formal raw output, or independent formal raw-audit result. Archival byte verification does not independently reproduce those test outcomes. No retained source, test, runner, auditor, container, or experiment was executed while preparing this archive.

## Formal disposition and ownership

The [October 1 #5082 disposition checkpoint](https://github.com/Unjuno/agent-interface/issues/5082#issuecomment-5922929392) retains **STOP / NOT STARTED** for the 4,096-publication overlapping-reader trial pending an exact exclusive assignment and refreshed source/image/output gates. The source PR remains open and Draft; Issue [#5082](https://github.com/Unjuno/agent-interface/issues/5082) remains OPEN. This archive does not advance the source branch, mark its PR ready, merge it, transfer a slot, or resolve a formal/research gate.

Keep allocation `needle-cross-process-publication-overlap-5066-v4-20260928-01` separate from construction checks and from the distinct OrbStack publication evidence already indexed elsewhere. Idle inventory, a successful construction container, CI success, or another lane's release is not an assignment to this allocation. Any later authorized execution requires the source owner's current disposition, [shared-resource coordination](https://github.com/Unjuno/agent-interface/issues/5085), current-main/freeze reconciliation, and immediate exact-engine/image/inventory/source/output checks.

The same October 1 checkpoint records that the separate writer-envelope/reader-exit missing-check hypothesis in [#5124](https://github.com/Unjuno/agent-interface/issues/5124#issuecomment-5861328531) was not reproduced and the issue was closed as not planned. That is not a publication-overlap result and does not close #5082.

## Claim boundary

The preserved [PLAN.md](PLAN.md) describes the intended hypothesis and decision gates, including 4,096 publications, four readers per arm, at least 32 qualifying open/replace interval overlaps across at least two reader PIDs, full provenance, and independent audit. None of those formal gates is established by this archive.

No filesystem atomicity, latest-generation freshness, linearizable version ordering, crash durability, cross-host/network-filesystem behavior, model/LoRA quality, GUI/task effect, runtime authority, production safety, latency, or product claim is added. Preserve all predecessor and competing construction evidence unchanged.

The archival placement follows the stable-path and scoped-evidence guidance in [CONTRIBUTING.md](../../../CONTRIBUTING.md) and [RESEARCH_METHOD.md](../../../docs/RESEARCH_METHOD.md). Under [CURRENT_GOAL.md](../../../docs/CURRENT_GOAL.md), this is evidence preservation, not completion of the unresolved experimental objective.
