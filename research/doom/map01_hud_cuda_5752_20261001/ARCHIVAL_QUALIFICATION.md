# Archival qualification: pre-candidate HUD allocation STOP

Reviewed 2026-10-02 for preservation only. Original PR #5757 head:
`12c55e4162dca2294eb972a0bdbabc2948721e4e`.

## Disposition and chronology

Preserve the original `STOP.json` byte-for-byte:
`STOP_VISIBLE_GPU_PROCESS_AND_REQUIRED_WAD_UNAVAILABLE` / `NOT_EVALUATED`.
The receipt reports candidate, auditor, CUDA workload, Docker/OrbStack, model/game/input effects and retries all zero; raw candidate SHA is null. It records LM Studio as a visible GPU process and a missing required local WAD. This review did not inspect the host or execute any source.

There are historical chronology/wording differences that are retained, not silently resolved:
- STOP.json records a start of 03:55 UTC and a stop at 03:58:44.6356637 UTC.
- The [queue allocation notice](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5924389042) gives a 04:00–04:20 UTC window.
- The [queue release](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5924457369) explicitly releases at 03:58:44 UTC after the start-gate STOP.
- A [later queue notice](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5924516946) describes allocation 01 as withdrawn/unconsumed before source freeze as main advanced, while reserving distinct allocation 02.

Those records consistently report zero candidate/auditor/CUDA work for allocation 01. They do not establish that its gate observation occurred inside the stated 04:00 lease. Do not infer current ownership, retroactive lease validity, execution, or a reusable reservation from them. The original receipt's terminal/no-reuse boundary remains intact.

## Static preservation checks

- The original STOP bytes reconstruct Git blob `3fb57a124fdf7429246e3af76998b454c5978761`.
- SHA-256: `6a3b6e331534d51d08c50ff31e7706059e97b10caaa2725cd39494a7f65f79ff`; JSON parses.
- `ORIGINAL_SHA256SUMS` binds that sole original file. This qualification and the manifest are additive.
- At main `f4fcea6a67f1d8695626447d97ae697fa454a04e`, this exact package root was absent; the current-main three-dot comparison contained only the original additive STOP file.
- Original-head hosted replay-gate succeeded; the unrelated formal job was skipped. Neither is a scientific test of this allocation.

## Separation from successors

This allocation is distinct from HUD allocation 02, later allocation 05 / PR #5979, and the ROI-size diagnostic. Successor evidence cannot retroactively change this STOP. The [#5752 evidence qualification](https://github.com/Unjuno/agent-interface/issues/5752#issuecomment-5942063746) also explains that the later timing loop omitted GPU complete-output decoding; do not turn that successor into a matched PNG-to-complete-output speed claim here.

Merging archives a pre-candidate STOP only. It establishes no HUD parity, speed, task effect or live-control result, closes no scientific owner issue, and authorizes no new allocation or experiment.
