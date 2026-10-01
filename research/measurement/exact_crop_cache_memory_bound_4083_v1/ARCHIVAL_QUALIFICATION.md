# Archival qualification: exact-crop cache construction and reconstruction HOLD

## Disposition and exact identity

This package preserves all 15 original files (99,047 bytes) from [source PR #5257](https://github.com/Unjuno/agent-interface/pull/5257), head `d1113617649336ee960c67e285743e7a331bdb3a`, at their original paths. Source package tree: `91881be885f38cdb2ff46dfaa092dd65ba7366a3`. Original bytes, mixed line endings, source declarations, environment metadata, failure summary, raw records, and recorded outcomes are unchanged. This separate note does not repair or normalize the originals.

Disposition: **historical construction/source preparation retained; source-to-receipt reconstruction HOLD**. Exact preservation is established; repository-reproducible execution is not. The historical 12/12 score-equality and 28,800-byte bounded RGB-payload claims remain attributed historical claims. No source, auditor, test, model, container, image generator, or experiment was executed during this archival preparation.

| Original file | Git blob SHA-1 | Bytes |
|---|---|---:|
| `CONSTRUCTION_AUDIT_FAILED_INITIAL.json` | `487d276b56ee4f6275c0bb7aa49770fb75a21b36` | 537 |
| `FORMAL_PREPARATION.md` | `f760c3c6edac1ea07293a2ac6eaceef524caadd9` | 1,757 |
| `FREEZE.json` | `724434006ac77c876fb0b9f35ebfcca6d4d274b3` | 3,131 |
| `README.md` | `9351ce3f3a327dbe8c83440c8954377d0751b550` | 3,015 |
| `audit.json` | `f8e3df7b0aed51744c5977119e8789c42a468657` | 313 |
| `audit.py` | `e88f033215596a14fc9fca8b191e4fe57ccc14d0` | 6,253 |
| `audit_formal.py` | `91f442774c33008a696bf3e02e59cfb253aa47a6` | 8,223 |
| `audit_v2.json` | `3a6ccdde6110df3af0e0cefe7bfcc8a9e9c16ca9` | 336 |
| `construction.json` | `190020825bef41c3cc2c8af0c2152251df138494` | 26,051 |
| `construction_v2.json` | `4bc9485352afd50894b81c9ded1afb9c667369ad` | 26,777 |
| `study.py` | `075cd2333d6e76bff01bfcee8a58684d512985fd` | 4,652 |
| `study_formal.py` | `d79cca1c8fd10a6e2cc4cd68ec5ec30c3f2b9cfb` | 5,677 |
| `upstream/candidate.py` | `993d983e05ddcd2a089cd8e63fa4a292b057b137` | 3,149 |
| `upstream/exact_crop_semantic_probe_v1.py` | `22a5c022d613039b0386535304cbc432009699af` | 3,957 |
| `upstream/inkscape_selection_frame_probe_v1.py` | `f4a68e95e6bbeb2896a00168f0c88282551be4e4` | 5,219 |

Each local file reproduces its original Git blob ID, fresh source-tree size/mode, and the prior review's SHA-256. Git blob verification identifies the committed bytes; it does not establish that those bytes produced the historical receipts.

## Retained observations and limits

- `construction.json` and `construction_v2.json` each contain 12 rows with equal recorded baseline/unbounded/bounded score objects, recorded maximum bounded RGB payload 28,800 bytes, and final unbounded payload 144,000 bytes. Reading these fields is a data-only consistency check, not independent execution or a new memory measurement.
- Both records describe ten 80×60 synthetic RGB images plus revisits to the last two, capacity two. The v2 raw retains Windows 11 build 26200, CPython 3.12.10, NumPy 2.4.2, and Pillow 11.3.0 metadata. These remain recorded provenance, not a reconstructed runtime.
- `audit.json` retains `PASS_CONSTRUCTION_SCOPED`, 108 checks, zero listed errors, and 4/4 control claims. `audit_v2.json` retains the same disposition, 96 checks, zero listed errors, and 5/5 control claims. Those receipts are historical claims subject to the source reconstruction and control-method limitations below.
- `CONSTRUCTION_AUDIT_FAILED_INITIAL.json` retains `FAIL_CONSTRUCTION_AUDIT`, 108 checks, a corruption-control error, and 3/4 controls. Its own evidence-origin field says this is a captured observed summary. The full original stdout/stderr and overwritten intermediate audit are not retained. The later receipts do not erase or repair that first failure.
- The proposed formal workload remains unrun: 64 unique 800×600 images plus eight revisits, 72 requests, capacity eight, proposed RGB-payload ceiling 11,520,000 bytes. The freeze records formal invocations zero, image digest null, runtime versions null, and pending exact shared-lane assignment. This is not RSS/application memory, throughput, GUI/model behavior, production adoption, or general LRU benefit evidence.

## Source/receipt reconstruction HOLD

All five `FREEZE.json` source SHA-256 declarations disagree with the exact committed files:

| Path | Declared SHA-256 | Exact committed SHA-256 |
|---|---|---|
| `study_formal.py` | `4b60febeed9d4dd9e45df664f2605a45b9a18e7f52dc2cf39b2c19259639c3c4` | `fd502de4bd09b4ab8f782834e399f2313508f76ed83a0f7f34eb516580ca0828` |
| `audit_formal.py` | `f7bc97715e11108f1e15bfb494b29d22059a17805d79b3c490a5d8b85dc210c1` | `55682d410d08b05200dfe1add662871ba37f715ab6f6f507e097ee6a7e807a00` |
| `upstream/candidate.py` | `4690a84ec967a8f2c83d931bacf0d440148815f740853bc0390050856f7b4d33` | `6686b1b0ac0bd065d9dd4a4dade6d6527ecec534e1e3a12e304d9eef3c159ae3` |
| `upstream/exact_crop_semantic_probe_v1.py` | `1e9d8405b562f4dcb6b305d486a3eefee1333f204e0c7ded13f3135a564de7cf` | `22e85fbc628dc713f121a4d023885f0b509912618a4bca715105285dd92af4b1` |
| `upstream/inkscape_selection_frame_probe_v1.py` | `ef2d1fbba8738ea743d85fc6a711e20e9ddd04a22007feee4b94f64e2524f22b` | `b7d21eb76741b84120730334f21ef0692c13f10b2a49064ca7386ae4d877ab42` |

All five `construction_v2.json` source declarations also disagree with the committed files. The three copied-upstream declarations additionally differ between this raw record and `FREEZE.json`:

| Path | Declared SHA-256 | Exact committed SHA-256 |
|---|---|---|
| `audit_formal.py` | `f7bc97715e11108f1e15bfb494b29d22059a17805d79b3c490a5d8b85dc210c1` | `55682d410d08b05200dfe1add662871ba37f715ab6f6f507e097ee6a7e807a00` |
| `study_formal.py` | `4b60febeed9d4dd9e45df664f2605a45b9a18e7f52dc2cf39b2c19259639c3c4` | `fd502de4bd09b4ab8f782834e399f2313508f76ed83a0f7f34eb516580ca0828` |
| `upstream/candidate.py` | `a90b37e7c85f9c6429289a4a978b9283ca8fb16a428ccf303f72221c58a9b1a7` | `6686b1b0ac0bd065d9dd4a4dade6d6527ecec534e1e3a12e304d9eef3c159ae3` |
| `upstream/exact_crop_semantic_probe_v1.py` | `1065a9d95d69e4547ff36da767e3b469baab628e87ec0a1951489059aa76425d` | `22e85fbc628dc713f121a4d023885f0b509912618a4bca715105285dd92af4b1` |
| `upstream/inkscape_selection_frame_probe_v1.py` | `1a532db9502f87b262c39eca50ad6620c58c71e5e3af0cc96ddd59902b906484` | `b7d21eb76741b84120730334f21ef0692c13f10b2a49064ca7386ae4d877ab42` |

The three `FREEZE.json` source Git blob IDs do match the preserved upstream Git blobs. Those Git identities and the differing SHA-256 declarations are distinct facts; neither should be silently substituted for the other.

The original README also retains these four nonmatching SHA-256 declarations, including the raw record's claimed identity:

| Path | Declared SHA-256 | Exact committed SHA-256 |
|---|---|---|
| `study.py` | `7ebcbadc02294143a4db7fc3d360b62faf028075c8a0764a37cdb9e0d91dbac6` | `7456d77e1c4c795d5b8b969631b6d33319bccc20d690ba2d7f34ef952e230ea5` |
| `audit.py` | `e58aa526515dbfc89ea8aaf9dc724480dc79ed3244652b422e734522baa0f30c` | `6e8f85e2000465fe1323efa85a4fbbf05f1cdf9fff6f5bc7a31e6b25dd6f9a42` |
| `construction.json` | `9910b4f8011c79ada7ec86144102960576f250593992bbee4e835cfa945b8e14` | `c2c5200bbb457dca26eda3833d48b5336ff38aa8fea84d457e43d52e32ffbedc` |
| `audit.json` | `aefaddca5d6161f3008a67c9e490d3a1c6d39bfdcc103416ff1ef945d15065ce` | `b1eaaad23eaf8c09ba127f8d79387b826ea9ac2e8797c61ab8777aadcf9c3b0a` |

The earlier data-only review found that deleting one final CRLF pair from each new formal script would recover its declared SHA-256. That observation is diagnostic only. This archive performs no such transform; all original line endings remain intact. The three upstream files were not reconciled by that earlier review's simple line-ending/trailing-whitespace comparisons. The cause of the source/receipt divergence is unresolved. Do not claim the retained audit PASS is reproducible from this repository package, and do not rewrite source declarations, raw records, or receipts to manufacture agreement.

## Auditor and control-method limitations

Static reading of the unchanged source establishes these limits without invoking any validator or mutant:

1. `audit.py` lines 95–109 tests hand-mutated copies with separate direct predicates. `audit_formal.py` lines 102–119 likewise counts bespoke lambda-predicate results; it does not submit the corrupted records through `validate`. The recorded 4/4 and 5/5 counts therefore do not demonstrate end-to-end rejection by the actual auditor.
2. In construction mode, `audit_formal.py` lines 52–56 iterates whatever `source_sha256` mapping is present. It does not require the exact expected source-key set. A complete provenance denominator is not independently enforced.
3. Intermediate bounded-byte checks (`audit.py` lines 69–79 and `audit_formal.py` lines 87–90) enforce an upper bound and entry count, without independently recomputing exact per-frame byte accounting for every row. Final-byte equality checks are separate and do not turn the intermediate declarations into independent measurements.
4. Both auditors import the retained upstream `score_path` implementation. The source's wording about independence must be read within that shared-scoring boundary.

No new counterexample was executed, no control was repaired, and no scientific conclusion is inferred from this source reading.

## Ownership, existing main, and remaining gates

At the 2026-10-01 readback, #5257 remained open/Draft, authored by Unjuno, with no assignees or requested individual/team reviewers. [Owner issue #5254](https://github.com/Unjuno/agent-interface/issues/5254) remained open and unassigned. Its latest [current-main/queue warning](https://github.com/Unjuno/agent-interface/issues/5254#issuecomment-5868408945) and [subsequent main-movement warning](https://github.com/Unjuno/agent-interface/issues/5254#issuecomment-5868415400) explicitly preserve the stale historical freeze and shared-lane STOP; they do not authorize a new formal run or promotion.

At inspected main `24f6b7d5f9395105807f981d48db212e6692a6f4`, the original package path is absent, corroborated by a direct Contents 404 and the complete measurement subtree. No exact package blob appears in the inspected measurement or experiments subtrees. Main retains the two exact upstream scorer files under `research/live_control/`; reused upstream code is not coverage of the original 15-file construction/provenance package. Coverage is complete for the measurement and experiments recursive subtrees and direct live-control source paths; the live-control listing is not a recursive namespace scan. This is not an exhaustive absence proof across every repository namespace.

Preserving this package does not ready, merge, or close the source PR; close #5254; reopen or spend an allocation; authorize Docker; or promote runtime/scientific claims. Any future work needs its own explicit ownership/authority and fresh current-main/source/image/output readback. The historical [#5085 queue request](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5868011186) is provenance, not a current lease. No fresh resource lease is asserted by this archive. Preserve the original #4083 evidence and missing-capsule/STOP history separately and unchanged.
