# Archival qualification: Issue #5494 / source PR #5497

## Preservation-only disposition

This additive qualification describes the five exact historical files from source PR [#5497](https://github.com/Unjuno/agent-interface/pull/5497), head `1bc9583b6dc54ca3f44045c81f8783fc9b5bfd9e`, branch `research/issue43-aoi-critical-retention-20260930-01`. Its recorded outcome remains **`STOP_RUNNER_OUTPUT_UNAVAILABLE`**. This is an infrastructure/provenance STOP, neither scientific PASS nor scientific FAIL.

The one post-freeze wrapper invocation exited 1 and returned no stdout or stderr. Whether the queue runner executed, the controls ran, or the independent auditor completed is unknown. No runner raw JSON or independent audit output is retained in these five files. No result, critical-retention advantage, AoI benefit, paired-policy comparison, or runtime conclusion is established.

This qualification does not resolve the original execution diagnosis/audit gap, close Issue #5494 or #43, or authorize another invocation. The original source/freeze/STOP commit chronology remains provenance; a final-file copy does not replace that history.

## Delivery-status reconciliation — 2026-10-02

[PR #6334](https://github.com/Unjuno/agent-interface/pull/6334) already preserved all five original blobs on main in merge `34f0880b160fd1bbedb7cde9112d38dd82690bf8`. [The owner's update](https://github.com/Unjuno/agent-interface/issues/5494#issuecomment-5942932407) explicitly keeps Issue #5494 open and the hypothesis unevaluated. Source [PR #5497 was administratively closed as superseded](https://github.com/Unjuno/agent-interface/pull/5497#issuecomment-5942876379), without merging it. Its historical branch ref returned 404 at this refresh, while source head `1bc9583b6dc54ca3f44045c81f8783fc9b5bfd9e` and its parent history remain resolvable. This records observed delivery status; it does not establish why or by whom the ref was removed.

The earlier [qualification proposal #6303](https://github.com/Unjuno/agent-interface/pull/6303), head `5e14a16038318c70fe5c07c56129506fb170ef14`, predates that delivery. Its keep-open/retain-branch wording is historical, not a request to reopen #5497 or restore the missing ref. This qualification-only successor adds no copies of the original files: only this explanation, its original-blob manifest and measurement-index navigation are new relative to current main. Preserve the linked PR/commit history and keep #5494/#43 open; no source ref is created, no original is repaired, and no study, test, auditor or transport sentinel is run.

## Exact provenance and inventory

- Frozen source main: `f09a0bd0a5a8d683a950df1b360670aaa1f194ca`
- Source commit: `dcecb4834ae03e6ec133b32eefbd7f42119913fb`
- Freeze commit: `4614468e94fe56fd0caf17cded0ed714af5a8355`
- STOP preservation commit: `21e4780314558d69bf03a5b9a053fc1fd5b85cb4`
- Original publication head: `1bc9583b6dc54ca3f44045c81f8783fc9b5bfd9e`
- Head's main-sync parent: `32db1c3fdc6e50dd6d64c3d6886e503c94144fd6`
- Five original files, **21,407 bytes**, already retained byte-for-byte by #6334; this qualification and the archive manifest are additive.
- The original FREEZE.json's `FROZEN_NOT_RUN` / zero invocation fields are the pre-execution snapshot. RUN.json is the later one-wrapper STOP record; neither is rewritten.

| File | Bytes | Original Git blob |
|---|---:|---|
| FREEZE.json | 1668 | `8756d597e1b75e593b6ca485d4d61a8345badc60` |
| README.md | 1686 | `eec783049cb88141b822ffc7fe91824e4323c4ea` |
| RUN.json | 1171 | `f284db9dd649a9f26f8c0c2a27d6a78188b55692` |
| audit.py | 8061 | `e0c227f3f157e963a97cb8dda0191344d4d67e37` |
| study.py | 8821 | `eda6af323a412767594d6e68dd6585688efb3023` |

## Separate transport sentinel

The [owner's preregistered command-transport probe](https://github.com/Unjuno/agent-interface/issues/5494#issuecomment-5911733743) and [result](https://github.com/Unjuno/agent-interface/issues/5494#issuecomment-5911751744) are separate from the queue study. That single sentinel invocation also exited 1 without stdout/stderr and remains `STOP_TRANSPORT_OUTPUT_UNAVAILABLE`. It neither recovers the earlier raw result nor establishes whether the earlier runner executed. The sentinel source/hashes are retained in those linked comments, not represented as additional files in this five-file archive.

## Static source caveat; no execution or repair

The original README documents piping study.py directly into audit.py. Static inspection shows study.py emits `study_source_sha256` but not `audit_source_sha256`, while audit.py lines 131–137 requires both fields. Therefore the documented direct pipe alone cannot satisfy that audit gate. The historical wrapper could have enriched the JSON, but no wrapper source is retained in this packet; this observation does **not** establish the cause of the historical output-unavailable STOP.

The study/audit accept expected source hashes from command-line arguments rather than independently hashing their own files. Archive integrity therefore depends on the pinned Git blobs and frozen source digests, not on interpreting self-reported runner fields as proof. Original source and instructions are preserved as historical evidence, not endorsed as an executable continuation.

## Lineage and scientific boundaries

- Prior [PR #5461](https://github.com/Unjuno/agent-interface/pull/5461) source/raw remain unchanged. [PR #5479](https://github.com/Unjuno/agent-interface/pull/5479) established `HOLD_INCOMPARABLE_DROP_ACCOUNTING`: the earlier 0.041 vs 0.001 and approximately 97.6% benefit are unsupported because the policies had identical transitions and counted different incoming event kinds.
- Older [Issue #1021](https://github.com/Unjuno/agent-interface/issues/1021) / [PR #1022](https://github.com/Unjuno/agent-interface/pull/1022) queue-semantics validation remains a distinct scoped result, not validation of #5494.
- [Issue #43's evidence gate](https://github.com/Unjuno/agent-interface/issues/43#issuecomment-5924745598) requires an observable, independently audited event-identity baseline before any arrival/service-envelope study. Do not retry or reinterpret #5494's frozen allocation; a successor needs a changed, validated execution/transport boundary.
- Main's distinct `research/analysis/aoii_observation_freshness_43_t0_v1/` packet remains `STOP_AUDIT_SOURCE_DRIFT`, with its supplemental audit separately qualified. It is not a substitute for this allocation.
- Scope of #5494 is a deterministic CPython 3.11.9 Windows-host synthetic queue: one session, capacity 4, horizon 200, one service slot/tick, 1,000 paired trials, seed 43001, 8% critical event probability. No calibrated GUI arrival stream, semantic classifier, planner consumption, independent task effect, latency/token benefit, GPU, Docker/OrbStack, or runtime authority is established. Discrete policy operation counts are not measured CPU time.

## Original preservation planning check — historical snapshot

Read-only inspection used main `0b8fcbd1ee8e1ac7c5ebfc137dcecd7226ea7477`. The original namespace was absent; complete measurement (3,957 entries), analysis (7,624), archive (11), archives (15), and docs (28) subtree listings contained none of the five original blob identities. Bounded all-state PR searches for #5497, #5494, and critical-retention found no competing archive. This is a targeted collision check, not a proof of global blob absence. The delivery-status reconciliation above supersedes namespace-absence and source-PR delivery status from that planning snapshot.

At the original inspection of the source head: one hosted `replay-gate` check succeeded; zero submitted reviews, zero PR conversation/review comments, and no legacy commit statuses. That unrelated replay gate is not a queue-study audit. [Exact check](https://github.com/Unjuno/agent-interface/actions/runs/36717579146/job/109894219529).

No archived program, test, auditor, experiment, or transport sentinel was executed to prepare this preservation. The read-only inspection and local packet preparation made no external-state changes; any later publication is a separate step.

## Initial #6303 publication refresh — historical snapshot

Before this separate archival Draft was prepared, main was refreshed to `d7e20a0d25e0c361d1e7cf56fd103f61fb927a2d`; the original #5497 head and #5494's five owner comments were unchanged, the source namespace was still absent, and repeated all-state searches found no competing #5497 / namespace archive. All 221 workflow YAML blob IDs matched the inspected complete trigger inventory. For this eight-path patch, the applicable executable jobs are the existing replay gate and Research Workspace Index; the broad #5716 construction and #4242 formal workflows have exact branch guards that exclude this archive branch. None selects the archived #5494 study or auditor. Hosted CI and independent review of the archival Draft remain separate from the original scientific STOP.

## Qualification-only refresh

The 2026-10-02 refresh independently matched all five main blobs against the source head and #6334: identities, sizes and frozen hashes are unchanged. The three-file current-main diff contains no original-source, freeze, STOP-record, workflow or runtime edits. Current workflow definitions were inspected before publication. The existing ordinary replay/index checks remain publication checks, not a queue-study audit. New exact-head review and ordinary CI are required for this qualification-only successor; the original scientific STOP and missing raw/audit output remain unchanged.
