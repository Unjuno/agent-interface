# Recovery review: #5056 allocation-04 byte preservation

## Retention decision

**RETAIN_EXACT_BYTES_AND_ORIGINAL_STOP_ONLY.** The original overall **STOP_PROVENANCE_OR_RUNTIME** remains unchanged. The retained runner-local `PASS_AUDIT_BOUNDARY_REPAIRED_SCOPED` is not the completed allocation decision: the independent audit failed and no final audit/manifest verification is retained. Qualification remains on hold, including unresolved cross-record namespace identity and historical process authentication.

This additive review dated 2026-09-30 preserves the 21 original Git objects and adds only this note. It uses exact-byte hashes, structured-data inspection and bounded archive decoding. It executes no repository source, auditor, test, canary, container, model, GPU or scientific allocation. No original byte, verdict or allocation is repaired or reused.

## Exact source and preservation map

Source: [PR #5056](https://github.com/Unjuno/agent-interface/pull/5056), original head [b62744bd331eee23d99061de6ec5e715a4d23308](https://github.com/Unjuno/agent-interface/commit/b62744bd331eee23d99061de6ec5e715a4d23308), tree `d1d7f352c519a38c25aaf17be3ef1052a4198fa4`.

The first commit [7c3f0cec129a9afbade030ab807594829e101d43](https://github.com/Unjuno/agent-interface/commit/7c3f0cec129a9afbade030ab807594829e101d43) has parent `e7a2cbe54cf5885044d103fff0a6a8f99adf908e`, exactly matching FREEZE's intake main. Its ten source blobs and FREEZE blob are unchanged at the result head. Every one of FREEZE's ten source SHA-256 declarations matches the exact preserved source bytes. This establishes retrievable Git/source-byte closure, not proof of the historical mounted source or execution order outside Git.

All original paths below remain under `research/analysis/predicate_order_audit_typehash_successor_r4_v1/`. Each current byte sequence reproduces the GitHub-declared length and Git blob. Publication reuses those existing blobs, including the opaque REPORT.md, rather than round-tripping content through text encoding.

| Relative original path | Bytes | Git blob | SHA-256 |
| --- | ---: | --- | --- |
| `CONSTRUCTION.json` | 1328 | `a86b23d1a575db70f6aa894dd648255de1cd9c6f` | `739e2cd1007048f4eba5795266606debe9570d99ef2be92908e029ddd833eb13` |
| `FREEZE.json` | 7619 | `4f4c2f7032bbc3576b909ec288a55cbedd2e78f5` | `e28b7af66a25757f809b1cbbce4fc34d2eac001ef9fd58c03228aadc65d65928` |
| `REPORT.md` | 869 | `bebe9d06d1164b06b64eb99f9eb0f03d9e7caab6` | `e3ec94518eb80a0c4f6a108ea009611d863fd33fffebdf270909a91bb11cdca2` |
| `input/RAW_AND_AUDIT.zip.base64` | 5326 | `c38dd2002f201d49b6fc261caff019550a4bf4bc` | `474b6381e8381ed8cae12141303e4638539d12cf6cf8b1c999c630efae80efe7` |
| `result/audit-audit.exit` | 2 | `d00491fd7e5bb6fa28c517a0bb32b8b506539d4d` | `4355a46b19d348dc2f57c046f8ef63d4538ebb936000f3c9ee954a27460dd865` |
| `result/audit-audit.stderr` | 743 | `ea70d57b6c8074b78a8006d11e754a185808283d` | `dbf64697f4ece9b56134c139ccc01aa71a2bc6e112b6c244b9599fb0407b2640` |
| `result/audit-audit.stdout` | 0 | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `result/formal-runner.exit` | 2 | `573541ac9702dd3969c9bc859d2b91ec1f7e6e56` | `9a271f2a916b0b6ee6cecb2426f0b3206ef074578be55d9bc94f6f3fe3ab86aa` |
| `result/formal-runner.stderr` | 0 | `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `result/formal-runner.stdout` | 36 | `4fc2b487c6bbe052d1ce172bff73cd2844602eca` | `50827c2edb071e2272a0eca191e8a1ed92018349efebc6b122bf3c654a58271f` |
| `result/formal-runner_result.json` | 3348 | `2e3b7609851dc3d5e087b8e63beffae0d82929e0` | `b2c6385685a6885f8cf8a414dc8b2dfc3df4723f5953486f3a148336d167f8f1` |
| `src/audit_entry.sh` | 155 | `2c5c263fa144db3a9bb71c6e4b590d25b27dbd15` | `087104abd40291ff575d55ed36f97ca24f97610c1ae239227bb1b7cb66326d16` |
| `src/audit_hardened.py` | 5975 | `b314562f69633f2d4771d531ee747d7a856db2e4` | `4da3d454175eb551de25901cec839a7fe62dfb14cdd86234b9b7caa2b7210178` |
| `src/candidate.py` | 1097 | `898f116f20df8dea3e59fd8e6e670b340ace0579` | `9b8a04cc0e5021953f29349e8d980e51a763a488df0c202aa27b1c97a280accd` |
| `src/formal_entry.sh` | 141 | `7e2b9e15ebf4074183b4b65581f8489fb1bf1060` | `cedc95ebaa47a615fe401ea59e5b6c4f66ae2a2e047a40b5b04b10ccde2dbeb1` |
| `src/independent_audit.py` | 4690 | `2fdeed6d18d94e335a598125627062bf9ba3c86a` | `36db3344836f3e7b76f55743ad6b328423ee6a1e592800250569fdf9a79a839d` |
| `src/manifest_entry.sh` | 161 | `85dce8d13262d684221127fa65e9f0ff2fc39159` | `6d0866c8c7a8b8fe1a1571f16fdf7602fa8e58465ca565c0d96041465a7f0c46` |
| `src/manifest_probe.py` | 2859 | `fd81bdd8eba50602f35b4f4f4f8c99e5f30a4a15` | `9ea4aa6f658fe9e8e8c4b42e94469679500bfe587a4e2cb0494e9b4634192dac` |
| `src/probe_baseline.py` | 1188 | `31f4a87f243c9aa74cc7f0ba96b964fdffe4e6fb` | `3f0e2b2b8bbd830f2beab93e322fb6e85247442e4b01d62be4a7146168dd87bb` |
| `src/runner.py` | 2999 | `c1d372b6b2e018510e94b0080cce14dc0923900d` | `70cafe2b8d5d673733a9c04c3332af5cf533afb6a095e5924f5f934ca6f8cf81` |
| `src/test_protocol.py` | 1296 | `c8c4425e99c38d9d17d26d2425100501cd8a8e6f` | `7ab6373f11282320058da0611285f732b6bff500c712228a2d4143334ee1d4f9` |

## Opaque report and transport boundary

[REPORT.md](REPORT.md) is preserved as exactly 869 bytes, Git blob `bebe9d06d1164b06b64eb99f9eb0f03d9e7caab6`, SHA-256 `e3ec94518eb80a0c4f6a108ea009611d863fd33fffebdf270909a91bb11cdca2`. It was retrieved from the exact public `download_url` supplied by GitHub directory metadata at the pinned source head. The unauthenticated byte download reproduced the expected length and Git blob before any decoding attempt.

Those exact bytes fail strict UTF-8 at byte offset 1 and have no observed UTF-8/UTF-16 BOM. Their encoding is **undetermined**. No alternate encoding is guessed, no readable report text is fabricated, and the object is not characterized as corrupt. The earlier text/base64 transport mismatch did not prove corruption of the original Git bytes. No claim in this note is derived from a purported interpretation of REPORT.md; factual descriptions below are limited to exact structured data, source text or explicitly linked historical statements.

## Allocation and namespace reconciliation

| Record | Identity and environment | What can be retained |
| --- | --- | --- |
| This PR's exact FREEZE | `predicate-order-typehash-20260928-04`; branch `research/predicate-order-audit-typehash-successor-r4-20260928`; r4 directory above; Docker Desktop `linux/amd64`; image `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9` | These are this Git package's declarations and match its actual source branch/path. |
| This PR's retained runner result | Schema `predicate-order-audit-typehash-formal-v1`, raw hash/size, baseline and seven canary records; **no allocation or platform/image field** | Bytes bind the reported raw input but do not independently authenticate allocation, host or process identity. |
| Issue #5018's earlier allocation 03 | `predicate-order-typehash-20260928-03`, r3 namespace, shell-path STOP before raw/canary work | A separate consumed predecessor; its receipts or source map are not substituted for r4. |
| Issue #5018's ARM64 allocation 04 comments | `predicate-order-typehash-arm64-20260928-04`; the same r4 directory spelling; different image `sha256:392307d22300de8b5986851a12d9176dfc0fc073e65bf6523ebd7dcbeb23564e`; `linux/arm64` | Distinct full allocation ID and incompatible reported process outcome. The comment reports OCI exit 125 before runner start, whereas this PR retains runner exit 0 followed by audit exit 1. These records are not combined. |

The ARM64 [preregistration](https://github.com/Unjuno/agent-interface/issues/5018#issuecomment-5859558780), [argv correction](https://github.com/Unjuno/agent-interface/issues/5018#issuecomment-5859615692) and [pre-run STOP](https://github.com/Unjuno/agent-interface/issues/5018#issuecomment-5859632849) cite local preservation commits and the r4 directory. This review does not possess a verified byte-for-byte ARM64 r4 bundle and does not infer that those local artifacts are this AMD64 PR. The shared directory/numbering creates a cross-record namespace ambiguity that remains explicitly unresolved. Exact commit, full allocation string and declared platform must accompany citations to this package.

The [later namespace-collision statement](https://github.com/Unjuno/agent-interface/issues/5018#issuecomment-5859831729) also separates an unpushed ARM64 r5 result from the canonical AMD64 r5 on main. At inspected main `f800808e3073894dcb72db46604deeb1623980e7`, the r4 directory was absent. The distinct [r5 FREEZE](https://github.com/Unjuno/agent-interface/blob/f800808e3073894dcb72db46604deeb1623980e7/research/analysis/predicate_order_audit_typehash_successor_r5_v1/FREEZE.json), blob `b667577c1dd6f768df79af55455f4d751aee2e11`, declares `predicate-order-typehash-20260928-05` and `linux/amd64`. Neither later r5 statements nor its artifacts supply missing r4 audit/manifest evidence or resolve r4 historical process identity.

## Structured input and runner evidence

The preserved base64 archive blob `c38dd2002f201d49b6fc261caff019550a4bf4bc` decodes to 3,991 ZIP bytes, SHA-256 `81f347c99c7461a210edf98437bd7f8ed298dd6f95070d0da4b447913d11a5c0`. Bounded in-memory ZIP/JSON inspection found:

- `RAW.json`: exactly 186,739 bytes, SHA-256 `5f48e0274f9fd800ac26af3dd70bd52171700b32ce159f3cdbe0f28c7ec35e7d`; 21 distribution objects containing 336 total row objects. These counts are static record counts, not a rerun of predicate-order calculations.
- Input `AUDIT.json`: 399 bytes, SHA-256 `55b91ba52c5df69adef809dd1ce721dbb9f59d807dc4c64a83b7cecfa9a1a181`; stored status `PASS_DRIFT_BOUNDARY_MAPPED`. This is a retained predecessor/baseline artifact, not the missing independent audit for allocation 04.

Both hashes equal FREEZE's input declarations. The raw size/hash also equal the retained formal-runner result. The preserved `src/audit_hardened.py` has the specifically required target blob `b314562f69633f2d4771d531ee747d7a856db2e4`. FREEZE separately names legacy blob `1a6cc0e46b32d4cd6989aed118d003cce4cfe399` as lineage context; it is not substituted for the verified target source.

The [formal runner JSON](result/formal-runner_result.json) stores baseline `PASS_AUDIT_HARDENING_SCOPED`, errors=[], 336 rows and 21 distributions. It stores seven canary records, each with baseline acceptance=true and candidate acceptance=false. These are historical recorded outcomes only; this recovery does not regenerate mutations, recompute their hashes, execute either auditor or independently establish their behavioral result. The [runner stdout](result/formal-runner.stdout) is exactly its decision label plus newline; the retained exit file is `0` plus newline and stderr is empty.

CONSTRUCTION.json explicitly labels its diagnostics as excluded, reports `formal_allocation_invoked=false`, and records earlier construction checks. FREEZE's zero invocation counters are frozen pre-run declarations. Neither record is rewritten to pretend it is an authenticated final process counter; the later receipts remain separately preserved.

## Independent-audit failure and missing gates

The retained [audit stderr](result/audit-audit.stderr) is 743 bytes and records `OSError: [Errno 30] Read-only file system: '/evidence/AUDIT.json'`. Audit stdout is empty; its exit file is `1` plus newline. FREEZE's audit command declares `/evidence` read-only, while the preserved independent auditor writes `/evidence/AUDIT.json`; static source inspection is consistent with the recorded failure. This consistency is not a re-observation of the container, mount, image or process.

The source attempts that write before producing its manifest. The 21-file bundle contains no completed new independent `AUDIT.json`, exact-path manifest, successful manifest-verifier result or completed negative-manifest-control receipts. The input archive's older AUDIT must not be used to fill this gap. No independently completed audit status is inferred from the traceback or from the runner's local PASS label.

The [original PR statement](https://github.com/Unjuno/agent-interface/pull/5056) explicitly retains overall `STOP_PROVENANCE_OR_RUNTIME` and the no-retry rule. That remains the preservation boundary. Current source/input hash closure resolves byte access, not these missing gates, opaque report interpretation, historical process proof or the issue's parallel r4 namespace ambiguity. This package is eligible only for transparent retention with those limits; it makes no new scientific, numerical, generalization or production claim.
