# Recovery notice: incomplete #4679 predecessor evidence

## Qualification

**HOLD_RAW_AUDIT_AND_FINAL_FREEZE_BINDING.** This is nonhistorical source/chronology preservation for [PR #4693](https://github.com/Unjuno/agent-interface/pull/4693), not verification of its reported capacity result. The historical `PASS_CAPACITY_CLOSED_GAP_SCOPED` label in RUN_SUMMARY.json remains unchanged as an author-reported outcome. The actual seed raw files and audit output are absent. Two historical attempted V2 freeze versions are now recovered, but their shared sidecar matches neither; final executed-freeze and process binding remain unverified.

This recovery review dated 2026-09-30 hashes exact published objects and reads structured declarations. It does not train, execute a model, run an auditor or test, reconstruct raw/process evidence, repair a declaration, select a preferred hash, or promote a scientific result. Preserve the original source branch and all eight current-head historical files unchanged. This proposal adds four archival paths holding three unique historical Git objects, plus this nonhistorical README.

## Immutable source and preservation mapping

Original head: [ac6ea480c6d0d603cfd0145f4013000d741bc062](https://github.com/Unjuno/agent-interface/commit/ac6ea480c6d0d603cfd0145f4013000d741bc062), tree `1ec855e96ab124f8c245daf61843a85ab7d28576`.

Original allocation: `needle-intent-capacity-4679-v1`; original branch: `research/needle-intent-capacity-4679-v1-20260927`; original path: `research/system1/needle_intent_capacity_4679_v1/`. All eight objects below reproduce their Git blob identities and SHA-256 values without byte normalization. Their original relative paths remain unchanged.

| Original relative path | Bytes | Git blob | SHA-256 |
| --- | ---: | --- | --- |
| `FREEZE.json` | 3750 | `f7bf9acb4941855d9ee29a840d81b222e77cd4d7` | `84b9143ddf40cae0c5e3356ce35d7e8178586e7e9a4a40643561aea3ed5a662e` |
| `FREEZE.sha256` | 65 | `fb07a40e32508a41b1496ef4e1eac867b8f3b4b7` | `e9867b4b08974aacc84491e7442e7994e3192c1c1d7a78ebd65a78c14f0a88d1` |
| `PREREGISTRATION.md` | 3641 | `e20aba82a57e4b3606fbae23c8cb9bd857fd1f8d` | `f0e5de78da48d11cac602d25eeffbee6bb46f9c307374cdba4e87f149cd571ae` |
| `PRE_FORMAL_CORRECTION.json` | 1556 | `fab03aa49d9ed4da21624034ec64f035bd34ba04` | `469d5273c62d481b170b13467a9643016c9d962b5727a9341ae20f21fc121c2c` |
| `audit.py` | 13616 | `6f4e3e5c27014fddc065ef82dd562b17f2c51f27` | `3512005c2fee3f0504453faeb4c6b3de467b57aa4142850452951344f2127500` |
| `formal/RUN_SUMMARY.json` | 1053 | `ecc9577e59a03e3fec22d592223aedc46cb1c717` | `78d1e7e36f59978d87bfe046b8f606342fe727352e4be9beac258be664edeb24` |
| `runner.py` | 8256 | `64ca157cf2dd8e47fa94f5f2ce3dac7346a85d69` | `85948fe1d8d286f7d866e80900902aa9609cc683ab876aa1ab12f93679460cd7` |
| `test_construction.py` | 3962 | `20c6e2af93616cbbb383d8a7c4b48d1a2c4e07cf` | `60372d9963c5c9c61aee84919f9480246e187309b2e7bbb2bd2e2c8ca933e80d` |

At the pinned original head, the source directory contains these seven root files and `formal/RUN_SUMMARY.json` only. The formal subdirectory has no seed raw, actual audit, stdout/stderr or process-exit files. A bounded search of main for the first declared raw hash found no published match; that search is not proof that no copy could exist elsewhere or outside GitHub.

## What current byte verification establishes

- The preserved 3,750-byte FREEZE.json hashes to `84b9143ddf40cae0c5e3356ce35d7e8178586e7e9a4a40643561aea3ed5a662e`, exactly matching FREEZE.sha256 and the [historical initial-freeze readback statement](https://github.com/Unjuno/agent-interface/issues/4679#issuecomment-5851981585).
- PRE_FORMAL_CORRECTION.json explicitly marks that initial freeze `SUPERSEDED_BEFORE_FORMAL_EXECUTION`. All four current source hashes match its separate `v2_source_sha256` map: preregistration, runner, audit and construction tests. The original auditor is unchanged; the other three current files differ from the intentionally preserved v1 source map.
- These are separate chronology stages, not permission to overwrite FREEZE or its sidecar with newer values. The [pre-formal correction statement](https://github.com/Unjuno/agent-interface/issues/4679#issuecomment-5851991042) promised a later FREEZE_V2/readback before execution; the current head omits V2 objects, but two complete attempted V2 versions are recoverable from intermediate commits and preserved below. Their declared freeze-hash binding remains unresolved.
- Current exact source-byte verification narrows the earlier publication caveat in the original PR. It does not establish historical mounted/executed-source identity, the final launch command, image identity, process results or raw-data integrity.

The initial runner guard problem and later SHA-as-tag launch failure remain historical descriptions. No stopped or consumed invocation is retried, and no local tag/image assertion is treated as a new verified observation.

## Recovered intermediate freeze history

Independent history review found two complete attempted V2 freeze objects that are absent from the final head. They are preserved under explicit historical version folders, without replacing any of the eight current-head files:

| Archive path | Original immutable source | Bytes | Git blob | SHA-256 |
| --- | --- | ---: | --- | --- |
| [`historical_sources/attempted_freeze_v2_00509f89/FREEZE_V2.json`](historical_sources/attempted_freeze_v2_00509f89/FREEZE_V2.json) | [00509f89/FREEZE_V2.json](https://github.com/Unjuno/agent-interface/blob/00509f8907e82bbfad4e0f0f8470c8aa7fc1fb1c/research/system1/needle_intent_capacity_4679_v1/FREEZE_V2.json) | 4151 | `e95d057134e8c7f0b12b717fb8c66ebf1ba7efd2` | `4e6c286b353e659fcb7986d390e57a16c91a05e05756f4650adca1961285b772` |
| [`historical_sources/attempted_freeze_v2_00509f89/FREEZE_V2.sha256`](historical_sources/attempted_freeze_v2_00509f89/FREEZE_V2.sha256) | [00509f89/FREEZE_V2.sha256](https://github.com/Unjuno/agent-interface/blob/00509f8907e82bbfad4e0f0f8470c8aa7fc1fb1c/research/system1/needle_intent_capacity_4679_v1/FREEZE_V2.sha256) | 65 | `41c1dd2779a0522c7d97510bbc32aaa8879f602b` | `26b401cc7975ed1f6c4a2247b0c0e58a69e7d3ceaa49405825e3b4a94de39bd6` |
| [`historical_sources/attempted_freeze_v2_5fd8917c/FREEZE_V2.json`](historical_sources/attempted_freeze_v2_5fd8917c/FREEZE_V2.json) | [5fd8917c/FREEZE_V2.json](https://github.com/Unjuno/agent-interface/blob/5fd8917c4c36460454a363c1736ec5aa1b237c0e/research/system1/needle_intent_capacity_4679_v1/FREEZE_V2.json) | 4151 | `379b1a96446f86fbe7be25bb60eb0a08c73e7a7d` | `a1b05f25b1171799eb74c777d2c3d1bdfaa312b5a6d98d4ab094a3c3a0cd8821` |
| [`historical_sources/attempted_freeze_v2_5fd8917c/FREEZE_V2.sha256`](historical_sources/attempted_freeze_v2_5fd8917c/FREEZE_V2.sha256) | [5fd8917c/FREEZE_V2.sha256](https://github.com/Unjuno/agent-interface/blob/5fd8917c4c36460454a363c1736ec5aa1b237c0e/research/system1/needle_intent_capacity_4679_v1/FREEZE_V2.sha256) | 65 | `41c1dd2779a0522c7d97510bbc32aaa8879f602b` | `26b401cc7975ed1f6c4a2247b0c0e58a69e7d3ceaa49405825e3b4a94de39bd6` |

Both 4,151-byte JSON versions have five-entry source maps that exactly match the current source and correction-file bytes. Both sidecars are the same exact 65-byte object declaring `f400334f84d1712cacf38e51b7b48a6a97cea18cd7ffc5ee1486c6c19ba6196f`; that declaration matches neither recovered JSON's actual SHA-256. The first JSON retains the literals `nosuiz` and `Numpy_initialization`; the second retains `nosuid` and `NumPy initialization`. No literal is changed and no cause or actor is inferred from those differences. Both environment image strings contain 65 hexadecimal characters, and both command arrays retain shortened image arguments and path placeholders.

Commit `5fd8917c4c36460454a363c1736ec5aa1b237c0e` also changes unrelated runtime content and deletes seven study files while retaining/modifying the attempted V2 records; the final source head restores the eight-file study. This proposal does not merge or cherry-pick that commit. It copies only the two precisely identified historical JSON blobs and shared sidecar to four clearly named archival paths. Repository history establishes byte provenance, not execution authenticity or which attempted freeze, if any, governed the reported run.

## Conflicting or incomplete declarations remain unresolved

| Subject | Exact retained declarations | Preservation boundary |
| --- | --- | --- |
| Third seed raw hash | RUN_SUMMARY.json records `fcee90f8277cd6d296a2e5cad3b38d65cf2c86d85c20d7b76e3d31c68ed3ce1e` (64 hexadecimal characters). The [result comment](https://github.com/Unjuno/agent-interface/issues/4679#issuecomment-5852092757) records `fcee90f8277cd6d296a2e5cad3b38d65cf2c86d85c20d7b76e3d31c68ed3ce1` (63). | The actual seed file is absent. Neither value is corrected or selected as an authenticated digest. |
| Image identity | Original FREEZE and the pre-formal correction declare `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e` (64 hex characters). The result comment and both recovered V2 JSON versions declare `sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a910e` (65). | These are unequal exact strings. No image-inspection receipt is retained here; no digit is removed or inferred. |
| V2 sidecar binding | Both recovered sidecars declare `f400334f84d1712cacf38e51b7b48a6a97cea18cd7ffc5ee1486c6c19ba6196f`; actual JSON SHA-256 values are `4e6c286b353e659fcb7986d390e57a16c91a05e05756f4650adca1961285b772` and `a1b05f25b1171799eb74c777d2c3d1bdfaa312b5a6d98d4ab094a3c3a0cd8821`. | Both mismatches remain. No reserialization or sidecar replacement is used to select a final freeze. |
| Frozen command versus historical launch | The superseded FREEZE's command arrays contain a shortened SHA-like image argument and source/output placeholders. Later prose says an image-as-tag launch exited 125, then a local tag was inspected and used. | The final expanded argv and process/image receipts are absent. The recovered attempted V2 versions do not authenticate the final expanded command or executed image. |
| Reported outcome versus retained evidence | RUN_SUMMARY.json records trainer/auditor exit 0, nine fits of 900 steps and `PASS_CAPACITY_CLOSED_GAP_SCOPED`; issue prose reports metrics and ten rejected controls. | These are summary/prose claims, not retained row-level data or the independently inspectable audit object. The historical label stays; it is not promoted to a verified PASS by this recovery. |

## Specifically missing original artifacts

The original RUN_SUMMARY identifies these files/hashes but does not contain their bytes:

- `seed_4153101.json`: `12861dba5247f2fd41cb903643a118b8c840aaaeaf4d581d73b7e2d233ea0a57`
- `seed_4153103.json`: `de1a08d265bcc46785a3466e3122e2ff922f0e8846f2719862bfd86dab7f1379`
- `seed_4153107.json`: the unresolved conflicting declarations above
- Actual audit JSON: declared SHA-256 `b3b5ea7082abcc866c736535e7e742d3d059ce50a32329eea5a5e96c7023f8c5`

Still missing are an authenticated final-freeze/readback binding and the actual trainer/auditor invocation, stdout/stderr, exit and image-inspection receipts. Complete attempted V2 objects exist and are now preserved; their unmatched sidecar does not establish that binding. A summary's numeric exit field is not a substitute for those original process records. No artifact is fabricated from expected values, recomputed from a new model run or replaced by another allocation.

Until exact original artifacts are recovered and independently bound, the width comparison, per-seed metrics, claimed ten-control audit and final process provenance remain unverified here. No numerical result, generalization, online adaptation, GUI behavior, action authority or production claim is established by this preservation.

## Why retain this predecessor

The distinct fresh-seed successor [PR #4783](https://github.com/Unjuno/agent-interface/pull/4783) was merged at `43368969c5fe9296057418d5ccd23da400615394`. Its [README at inspected main](https://github.com/Unjuno/agent-interface/blob/fc1fb8a798bb8635c2dbd05d818b9fbfb85c8e9c/research/system1/needle_intent_capacity_4679_v2/README.md), blob `138348e1721d136ca67bb0a43b936ffdc7d97994`, explicitly identifies #4679 as its predecessor and says the original data/result/audit remain unchanged. Its retained frozen disposition is `STOP_AUDIT_INTEGRITY`; the separate corrected-auditor result is labeled post-hoc exploratory analysis.

That successor uses different seeds and cannot replace any missing v1 raw, freeze, audit or process record. Its integration does not verify the original capacity PASS, and this v1 preservation does not relabel the successor. The original v1 directory was absent at inspected main `fc1fb8a798bb8635c2dbd05d818b9fbfb85c8e9c` and package-intake main `571c87775c631b4500d6da659a238762dc3fb665`.

Retaining this qualified source/history bundle prevents the already-linked predecessor from being mistaken for a complete verified experiment. Publication scope is the eight unchanged current-head objects, four archival paths for the two attempted V2 versions and their identical sidecars, and this qualification README: thirteen paths total. No unrelated commit is integrated, source edited, missing evidence reconstructed, allocation retried or scientific result promoted.
