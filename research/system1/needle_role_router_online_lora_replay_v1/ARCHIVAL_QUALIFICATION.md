# Archival qualification — Issue #4899 / source PR #4906

This is additive preservation of an existing research record, not a new experiment, a repaired registered audit, or a promotion. The 17 original files from [source PR #4906](https://github.com/Unjuno/agent-interface/pull/4906) are retained at their original paths using their exact Git blobs from commit `30c4a4d867484b0f7c9687ee78de9f5a0e71d49c` (original directory tree `7c5b080cf753809ab8431a4ba03bf2eea06b75cb`). This qualification is separate from those original bytes.

## Registered disposition and scope

- The sole frozen formal allocation remains **`HOLD_AUDIT_INTEGRITY`**. Its original auditor reported the three `base_row_indices:digest` errors, one per seed; neither that auditor nor the raw or registered report has been rewritten.
- The relative quality gate remains missed: on seed `736211`, separate-skill A=1.0 ties `SHARED_A_REPLAY` A=1.0, so it does not achieve the preregistered +0.10 A gain over every shared arm on every seed. Preservation cannot turn this result into a PASS.
- The later [#5172 / PR #5204 post-hoc audit](../needle_role_router_online_lora_audit_v2_20260928/posthoc/POSTHOC_AUDIT.md) separately reports zero integrity errors after the schedule-contract check and a `FAIL_ROUTING_OR_RETENTION` scientific diagnostic. It explicitly reuses the frozen auditor's trajectory-replay functions, rather than a second independently implemented model-replay engine. That successor diagnostic does not reclassify the original HOLD.
- [Issue #4899](https://github.com/Unjuno/agent-interface/issues/4899) remains open. Retaining the archive does not complete the research question, authorize another run, or reopen any consumed allocation or seed.
- No natural-language routing, live Needle/agent utility, transfer, end-to-end latency, safety/action authority, runtime behavior, or production readiness is established by this archive.

The historical [README](README.md), [preregistration](PREREGISTRATION.md), [freeze](FREEZE.json), [construction report](CONSTRUCTION_REPORT.md), and [formal result](evidence/formal_01/FORMAL_RESULTS.md) remain unchanged. Their historical run instructions and future-step wording are not authorization to execute them as part of preservation.

## Why retain the original paths

Before this preservation, main already contained [PR #5204](https://github.com/Unjuno/agent-interface/pull/5204)'s nested [predecessor source capsule](../needle_role_router_online_lora_audit_v2_20260928/posthoc/predecessor_source.zip.b64) and [formal evidence capsule](../needle_role_router_online_lora_audit_v2_20260928/posthoc/formal_01.zip.b64). Byte inspection recovers 16 of these 17 original blobs from those capsules: 14 original top-level files, the exact formal ZIP, and the formal results document inside that ZIP. The missing item was the full `evidence/construction_r4.zip`; the source capsule retained its engineering-history document but not the full construction bundle.

This archive restores navigable original paths and that missing committed construction ZIP. It does not replace, rewrite, or invalidate the successor capsules or reports.

## Archive identities and coverage

| Artifact | Bytes | Git blob SHA-1 | SHA-256 |
|---|---:|---|---|
| `evidence/construction_r4.zip` | 152884 | `3ab48e2778f7534a0130352dcd28ca8c593d6f90` | `40ec7450cab6b55a12f8d2bbb3892b11399c6e5115554d864e776dc02cc57958` |
| `evidence/formal_01.zip` | 447841 | `e0d125861ea39171438447875a9575bd956bebe2` | `e205de318c0f17541b5b075ae145707645bb67458d7ed07ba397982d78833aeb` |

The formal ZIP contains the original raw, trainer and auditor invocation receipts, stdout/stderr, audit report, and formal results document. Its `raw/formal_result.json` remains 1,611,168 bytes with SHA-256 `7ff93c67a4bc8e9f864511f1b89bf4fe2109287fd359927fee51de345c10188b`.

The construction-r4 ZIP contains final r4 raw, the construction and audit invocation receipts, their stdout/stderr, the final audit report, construction-test log, and `history/ENGINEERING_ATTEMPTS.md`. The r4 raw remains 537,401 bytes with SHA-256 `ca38d07392a8ef5a9df3fdf3c252b24eea62d129648d2a12bc1e760f78d5d4e7`. The r4 `PASS_CONSTRUCTION_AUDIT` is an excluded-seed construction finding, not formal inference.

**Earlier construction coverage is incomplete.** The historical report and bundled history say the original r1/r2/r3 outputs and auditor reports were kept in separate local output folders. Those full earlier raw/report sets are not included in the 17 committed files, the predecessor source capsule, or `construction_r4.zip`; their current local availability was not checked by this preservation. The archive preserves the disclosures: r1 `STOP_A_SKILL_MUTATED`; r2 audit failures; and r3's invalidated PASS under a faulty route expectation. A history summary and the final r4 ZIP are not a recovery of all earlier raw evidence.

## Inherited receipt line-ending distinction

The two construction invocation receipts inside the ZIP retain CRLF bytes. Their SHA-256 values match the exact-byte values recorded in `FREEZE.json`, but that freeze's internal Git blob IDs match LF-normalized versions of the receipts instead of the ZIP-member bytes:

| ZIP member | Exact ZIP-member Git SHA-1 | Recorded Git SHA-1 (matches CRLF-to-LF normalization) |
|---|---|---|
| `CONSTRUCTION_INVOCATION.json` | `95e7c20d22501fc8d1ab000872781de5556dcb4e` | `8a65121dadf150c67513e3f456692674bd32e263` |
| `audit/CONSTRUCTION_AUDIT_INVOCATION.json` | `8d2f92d16ab11c4a520c6da720e73176d9ace25d` | `98e58512f03ac4ca9278b50d5b418196cb99b11f` |

This is an observed distinction in the inherited metadata, not a repair or new audit conclusion. No line endings or recorded identifiers were changed. The original construction ZIP itself still exactly matches both its recorded Git blob and SHA-256 identities.

## Exact original blob map

All paths below are relative to this directory; every original entry has mode `100644`.

| Original path | Git blob SHA-1 |
|---|---|
| `CONSTRUCTION_REPORT.md` | `54c61ac4c579bc5fae934a67b4722ca0079e3ee3` |
| `FREEZE.json` | `c5e29f535b4e9959fd5274ade4128e3c04da6c62` |
| `FREEZE.sha256` | `a7a337fc499f96ad9ea6a73649922625902d7efd` |
| `PREREGISTRATION.md` | `49aebce6f7771a2fbbac1fb4765f7b358f2618fe` |
| `README.md` | `4897648be0596dc65fd44bba4443932cf8b289bc` |
| `audit.ps1` | `8578eb27f5546a6e7cd04eb27052b1d8c527706c` |
| `audit.py` | `c9c57cf08b582a856708f59bbdd23debb4975881` |
| `construction.ps1` | `b86bd4afadb6a7030b880b49e908802c2880a3ac` |
| `construction.py` | `2f25bef79c17554daddbc769d588ccf73c804f94` |
| `construction_audit.ps1` | `f21ae5b7b02c77418bfba582eaf2d17c4202e4d3` |
| `construction_audit.py` | `9f58f109332d89cfa67393f8186fb6d2428de852` |
| `evidence/construction_r4.zip` | `3ab48e2778f7534a0130352dcd28ca8c593d6f90` |
| `evidence/formal_01.zip` | `e0d125861ea39171438447875a9575bd956bebe2` |
| `evidence/formal_01/FORMAL_RESULTS.md` | `468f76a026a68209d8318bd90591301c177d6723` |
| `formal.ps1` | `f6015aa3fe20de3a0631bd3c0c6c8c8779e3057c` |
| `runner.py` | `1633cf300df349f94d333bfcbe38257b1657f009` |
| `test_construction.py` | `832b051c6e057c51d77703fabde98a2ea17660e5` |

## Preservation verification boundary

Verification was limited to read-only source/metadata inspection, local base64 decoding, archive-member inspection, and byte/size/Git-blob/SHA-256 comparison. The two ZIPs and all 17 original blobs were checked; the frozen source hashes, strict freeze sidecar, and recorded raw/receipt/report identities were compared as data. No old trainer, auditor, test suite, Docker wrapper, model, optimizer, or experiment was executed. These preservation checks are not a rerun of scientific validation.
