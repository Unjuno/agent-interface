# Allocation #01 STOP reconciliation

Date: 2026-10-01 UTC  
Allocation: `GPU-HUD-CUDA-5752-20261001-01`  
Scientific status: `NOT_EVALUATED`

## H / T / D / C / U

**H.** The CUDA HUD-parity/speed hypothesis in #5752 remains untested.

**T.** This note reconciles the earlier pre-candidate record in [REPORT.md](REPORT.md) with the allocation owner's contemporaneous records. The authoritative STOP and release are in [#5752 comment #5924457185](https://github.com/Unjuno/agent-interface/issues/5752#issuecomment-5924457185) and [#5085 comment #5924457369](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5924457369).

At 2026-10-01 03:58:44.6356637 UTC, before candidate launch, the explicit gate returned `STOP_VISIBLE_GPU_PROCESS_AND_REQUIRED_WAD_UNAVAILABLE`. The observed RTX 3080 snapshot was 0% / 9 MiB, but `nvidia-smi` identified PID 11508 (`LM Studio.exe`, C+G), which satisfied the visible-GPU-process STOP condition. The pinned local `_vizdoom/vizdoom/freedoom2.wad` was also absent. No process was terminated; no WAD was downloaded or substituted.

**D.** The allocation owner's retained record is controlling: candidate=0, independent auditor=0, CUDA workload=0, Docker/OrbStack=0, scientific outcome `NOT_EVALUATED`. GPU inventory *was* queried; the earlier [REPORT.md](REPORT.md) incorrectly stated GPU queries=0 and named source/auditor-freeze incompleteness as the allocation's typed STOP. Its 04:02 relinquish time was also wrong. The slot was actually released early at 03:58:44.6356637 UTC. Preserve that earlier report unchanged as a separate intake observation; do not use it as the authoritative allocation disposition.

**C.** The stale intake base (`bf0edd75ff5f12a8c5cddb0e0d74d9abcd9957a8`) versus then-current main (`8827fad422b225bddd9b1c6d34bfa68ca19265c5`) was a recorded provenance concern, but the operative STOP was the visible process and absent required WAD. The earlier report's workspace search was not the allocation owner's complete machine preflight and must not override the contemporaneous STOP receipt.

**U.** No conclusion about parity, speed, or HUD usefulness follows. The fresh #02 allocation recorded in #5752 is a separate window and has not been inspected or used by this reconciliation. This work performed GitHub reads/writes only; it made no GPU, Docker, model, GUI, game, or input calls.

## Issue state

PR #5763 merged at 04:07:41 UTC and GitHub marked #5752 completed at 04:07:42 UTC, even though the issue body retained a fresh #02 allocation window and no scientific result. The PR body contained a negated “does not close #5752” phrase; GitHub appears to have treated the closing phrase as a directive despite the negation. #5752 was reopened at 04:10:21 UTC. Future PR descriptions should avoid close-keyword-plus-issue-number wording when no issue state transition is intended.

