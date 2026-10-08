# Archival qualification: invocation-boundary T0 first STOP

## Disposition and immutable origin

Preserve all 11 published files from [source PR #5604](https://github.com/Unjuno/agent-interface/pull/5604), head `4da05935e786ece4557fb05989d43cc725d0ee95`, directory tree `dd786ca252aad7ac43a0870a23155401ad798491`. Originals total 25,241 bytes. Exact paths, 100644 modes, source blobs, hashes, and the CRLF bytes in both retained result files remain unchanged. This note does not change the first outcome.

Disposition remains `STOP_INVOCATION_BOUNDARY_AUDIT`. Archival delivery is not a PASS, corrected audit, independent reproduction, new invocation, or evidence of historical allocation compliance.

## First outcome and limitations retained

[RESULT.md](RESULT.md) and [EXECUTION.json](EXECUTION.json) record Windows-host CPython 3.12.10 construction: seven prefreeze tests, one candidate invocation exiting zero with eight rows, then one separate auditor invocation exiting one. Only five of six declared controls rejected. Read-only inspection found the positive-row mutation wrote the PASS label already present, so it was a no-op. No retry is recorded; the candidate/auditor allocation is consumed under its no-retry rule.

The original [README.md](README.md) says five negative/corruption conditions, whereas FREEZE/RESULT/AUDIT and the auditor's six appended controls use six. Preserve that denominator inconsistency; the controlling retained audit reports 5/6 and STOP.

The retained raw SHA-256 is `d3fb121b95d95fa61ea771a7dd0c20a8e255ea83b72752a3ebe371b27762d4b2`; retained audit SHA-256 is `7ade1dcddb23cb9249f57e27e1e14c0f2ba1bc27a585c6b19231af986dba4331`. The historical Allocation 04 fixture emits `invocation_count: null` and `STOP_INVOCATION_PROVENANCE_OR_BOUNDARY`. Several artifact references do not prove an exact number of historical invocations. No IDs/counts are assigned retroactively.

The freeze's `frozen_main` (`575c536027aafa949dc673ff4c5a1a692fa4a38a`) differs from the source PR's recorded latest-main branch parent (`9fc98feb617c26fe1baa7ecc4decd43b69df8601`). Preserve both identities as separate recorded stages, without silently treating them as the same execution provenance. Byte verification does not independently establish host/process chronology.

## T1 successor is separate

[PR #5610](https://github.com/Unjuno/agent-interface/pull/5610) merged a separate [T1 audit package](../invocation_boundary_5156_t1_20261001_01/RESULT.md) at merge commit `dd1f9382ea20d15629516bb0dd995f4a4f1e4f32`. T1 retains the same input and raw Git blobs and records its corrected audit's 6/6 control result. It does not contain this original T0 auditor, all original source/report files, or the original failing receipt. T1's reported PASS does not overwrite T0's STOP, upgrade T0's allocation, or resolve Allocation 04's unknown count.

## Coverage and static verification

At inspected main `4cf0a3dfde1219671b671bf0a9079a11dcb2e159` on 2026-10-01, the T0 namespace was absent even though T1 was present. Complete nontruncated source-tree metadata and reconstructed blob identities verified all 11 originals; all four frozen source hashes and all ten SHA256SUMS entries matched. The current-main T1 inputs/raw blobs match their T0 counterparts. No source, test, runner, auditor, oracle, or mutation control was executed in this preservation work; JSON and source syntax were parsed as static data only.

## Owner and claim boundary

The host-only provenance fixture provides no real X11, key-up timing, physical occupancy, container-allocation compliance, MAP01/task effect, safety, or runtime promotion. It grants no shared-container resource lease. The [#5156 owner gate](https://github.com/Unjuno/agent-interface/issues/5156) and its [latest inspected nested-bracket limitation](https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5939309038) remain distinct.

Source PR #5604 was open/Draft at inspection. This archive does not ready, merge, close, reopen, or delete that PR/ref, rerun the consumed T0, or authorize a successor allocation. Refresh current owner, source, and main state before later publication or disposition.
