# Issue #5752 pre-candidate STOP

Date: 2026-10-01 UTC  
Disposition: `STOP_SOURCE_AND_AUDITOR_FREEZE_INCOMPLETE`  
Scientific status: `NOT_EVALUATED`

## H / T / D / C / U

**H.** Issue #5752 hypothesizes that a CUDA implementation of the existing Freedoom HUD reader can exactly reproduce the CPU reader on 19 retained v38/v39 frames and achieve at least a 2x warm per-frame speedup. This allocation did not test that hypothesis.

**T.** The authorized allocation `GPU-HUD-CUDA-5752-20261001-01` was bounded to 2026-10-01 04:00–04:20 UTC and explicitly prohibited Docker/OrbStack, model/provider, GUI, game, and OS input. Its recorded freeze was main `bf0edd75ff5f12a8c5cddb0e0d74d9abcd9957a8`. At 04:02 UTC the current main ref was `8827fad422b225bddd9b1c6d34bfa68ca19265c5`; read-only ref inspection showed the allocation branch `research/gpu-hud-cuda-5752-20261001-01` still pointed at the older freeze. No issue-specific candidate/independent-auditor source freeze or retained input/output manifest was available in the accessible task workspace. The source, input, hash, and output gates therefore could not be established before candidate launch.

**D.** Typed STOP before candidate. Candidate invocations: 0. Independent auditor invocations: 0. GPU queries or CUDA operations for this allocation: 0. Docker/OrbStack operations: 0. The unused allocation window is relinquished as of 04:02 UTC; it is not transferred to another issue by this record.

**C.** This is an allocation/preflight disposition only. It is not evidence for or against CUDA parity, speed, or HUD usefulness. No retained image, source, GPU state, or prior #503 result was modified or reclassified.

**U.** The HUD hypothesis remains `NOT_EVALUATED`. Any successor needs a fresh current-main source/data freeze, independent auditor, exact outputs, and a separately assigned bounded GPU slot. The issue's no-Docker restriction remains specific to this experiment; this STOP does not authorize use of Docker Desktop.

## Provenance

- Current-main observation: `8827fad422b225bddd9b1c6d34bfa68ca19265c5`.
- Allocation freeze and allocation-branch ref: `bf0edd75ff5f12a8c5cddb0e0d74d9abcd9957a8`.
- Coordination record: [Issue #5085](https://github.com/Unjuno/agent-interface/issues/5085), comment #5924389042.
- Scientific hypothesis: [Issue #5752](https://github.com/Unjuno/agent-interface/issues/5752).
