# Preservation review: complementary #5492 host-control record

## Purpose and limits

Preserve **PASS_KEY_IDENTITY_AUDIT_HOST_ONLY** and **PASS_INDEPENDENT_RAW_ONLY_AUDIT** exactly as recorded by [closed, unmerged PR #5492](https://github.com/Unjuno/agent-interface/pull/5492), without rerunning, replacing, combining or upgrading either result. Preservation disposition: **RETAIN_COMPLEMENTARY_HOST_CONTROL_EVIDENCE_ONLY**. Acceptance of the selected [PR #5489](https://github.com/Unjuno/agent-interface/pull/5489) remains a separate review decision.

This static review dated 2026-09-30 used exact-byte hashing, manifest comparison and JSON parsing. It executed no repository source, new comparator, mutation control, test, container, X11/InputOwner action or scientific allocation. Current byte closure does not independently authenticate historical execution, environment, source mounting, invocation count or process isolation.

The #5492 result includes an omitted-row control and a separate decision-record audit. It is useful complementary evidence, but belongs to #5492's own candidate source and host run. Archiving or linking it does not show that the different #5489 candidate executed or passed that control. No live X11 release interval, physical key-up, held-input occupancy, MAP01, useful feedback or recovery claim follows.

## Reconciliation status at intake

- [Issue #5486 reconciliation comment](https://github.com/Unjuno/agent-interface/issues/5486#issuecomment-5911326322) identified #5492's missing-row control and separate auditor as complementary to the seven-case #5489 run.
- [Issue closure](https://github.com/Unjuno/agent-interface/issues/5486#issuecomment-5911388981) and [PR closure](https://github.com/Unjuno/agent-interface/pull/5492#issuecomment-5911388642) subsequently selected #5489 as the sole integration candidate while preserving #5492's branch.
- The latest inspected [reopening comment](https://github.com/Unjuno/agent-interface/issues/5486#issuecomment-5911473437), posted 2026-09-30 12:39 UTC, explicitly states that the required omitted-row gate has not been integrated into #5489 and reopens the issue. Its acceptance gap is not silently closed by this archival note.
- The [#5489 independent-check comment](https://github.com/Unjuno/agent-interface/pull/5489#issuecomment-5911345611) is a separate historical report. Its stated CRLF normalization and comparator/test execution were not performed or generalized to #5492 here. All #5492 hashes below matched exact published bytes without normalization.

## Immutable origin and exact preservation mapping

Original #5492 head: [0cd0c56681eee47e81852d29a2f461c81c319d03](https://github.com/Unjuno/agent-interface/commit/0cd0c56681eee47e81852d29a2f461c81c319d03), tree `8c47f46797bdc7194323054311fad05082ba27e9`. Original scope is Issue #5486, successor of #5156; its retained host record is `results/host-01/` under `research/live_control/owner_keyup_key_identity_5156_v1/`. That identity is preserved; no new allocation identity is invented.

Every original file retains its exact original path and bytes. The following 15 files independently reproduce their source Git blobs and SHA-256 values. This note is the only new file in this preservation package.

| Relative original path | Bytes | Git blob | SHA-256 | Relation to #5489 |
| --- | ---: | --- | --- | --- |
| `FREEZE.json` | 1860 | `8d10aa74fa54740fb7faaa86745db20b4c3e7406` | `6a3fb477817750be01232ce9e94746a607655577d5fb896fcc064649d0163137` | complementary object |
| `FREEZE_AMENDMENT01.json` | 711 | `f73ae758277fa2272e6426a4ae4ec8464ec57097` | `1bed31b4c6e72a5f5c44440f24bdffaed2ce476c4724bbe14e46fb41df4a830a` | complementary object |
| `PLAN.md` | 1606 | `87f9b4b9c0328d1ad5c1c0033e36a37e07b49af9` | `5129d72b52ab7357cfba254977d32e3330843db847e5e42b33db4c4d544fe6e2` | complementary object |
| `audit_key_identity.py` | 4073 | `05908365ddb19baf19e5a80890e8f882dc13346b` | `79f95eadb29bc6cc35036c6ff424cb284e55849ecd76ccd2a841ae186a18d1cf` | complementary object |
| `expected_inventory.json` | 519 | `affa71e53457bb903353ce67b3477ef20b1d488c` | `9ef72a837ce4f5d802dcc7fdb72a843a0e768154dbe30897a00f270cfaabde2b` | shared input |
| `independent_audit.py` | 1550 | `0a816ec31a9df8dc6a61e01188e36a0e16a1d102` | `da6804eb3d1344efedd47d95b4287e5903a75692093892b55c27360eb32f61f5` | complementary object |
| `independent_audit_v2.py` | 1602 | `6d1ed053185919d3f646db98b96a82a7d4fba487` | `79758680c8dd37cd604903c84a317ebdfb22f07ec9471bfe962428efbdc2ba3d` | complementary object |
| `input_raw.json` | 1344 | `451247a5180348b8c29d09994dc0264f822585d1` | `56842934b9f9b13fe0e52d515d31bd0c3d598cdb1cfa8b719dfb4c8ba463cbc2` | shared input |
| `legacy_audit_reference.py` | 3906 | `c37b6372f4e5a7306b98049c834559fdd60cadee` | `191fdabdd289e49b03514d1dfc66ba475b885ab078b733a7ef7030daf9cfe906` | shared input |
| `results/host-01/AUDIT.json` | 941 | `9e7e254bc354205ce893d2dd4ad83f9b153e190a` | `58f594ce4105074f4222cb913af787520261267f904ec8c30f06e8fa6fde92bb` | complementary object |
| `results/host-01/AUDIT_COMMAND.txt` | 94 | `edbad68a037050e3d083b311ad063be77edad1e1` | `d239416d3add265d8feab5d9357301843cd1231e6652c124fd01e62c030cc439` | complementary object |
| `results/host-01/RESULT.md` | 1673 | `789b686e36aee2d12f6ef78a5551462924eddd89` | `5e8c03e7cad1862db403fff30b177c46ddee3efdea82929aa3a545c03dfe1de6` | complementary object |
| `results/host-01/RUN.json` | 2848 | `dfcc1ab335d9f1e232456601005cd9e764daa158` | `d2835ff561428ec83eb11b1f3d6da51f81f67822361609acc67d52d670a632ce` | complementary object |
| `results/host-01/RUN_COMMAND.txt` | 132 | `99f6301ed4d1ebe7ba98edf269b7bf663061d1f3` | `15dc6efd010687590facacfd342b0f127d57cc40f20b6f2bcf8d7b70ad0d4492` | complementary object |
| `run_key_identity.py` | 3108 | `770d7ccb82c09ea4ac60db060ccde7563308028b` | `044465ed408dde88d680e24d05ff507ec8564756a297da4edecbcd767017b20c` | complementary object |

The comparison used #5489 head [82327db213b8fbd4d2d4c86dd312a26ebb792ab1](https://github.com/Unjuno/agent-interface/commit/82327db213b8fbd4d2d4c86dd312a26ebb792ab1), tree `edc2a40e8ca4217baf5a6538e31c0ba43a48b57e`. Its complete 11-file changed-path inventory has exactly three identical input objects:

- #5492 `legacy_audit_reference.py` equals #5489 `research/live_control/owner_keyup_audit_key_identity_5156_v1_20260930/baseline_audit_v2.py`, blob `c37b6372f4e5a7306b98049c834559fdd60cadee`.
- #5492 `expected_inventory.json` equals #5489's same basename in that directory, blob `affa71e53457bb903353ce67b3477ef20b1d488c`.
- #5492 `input_raw.json` equals #5489 `raw_input.json`, blob `451247a5180348b8c29d09994dc0264f822585d1`.

The other 12 #5492 objects, including both result receipts, freeze/amendment, candidate/runner and independent-auditor versions, are not present as identical objects in #5489's 11-file contribution. Keeping the three shared inputs at their original #5492 paths maintains a self-contained immutable provenance bundle; it does not count them as new evidence.

The original #5492 directory is absent at both that #5489 head and inspected main `e7a68325c06385a8dc61d41ca33802cbe22678e4`. None of its 15 blob IDs occurs in the four `owner_keyup_*` lineage directories present under `research/live_control` at that main ref. This is a bounded lineage/path check, not a claim of an exhaustive repository-wide identical-blob search. The three original #5467 paths named in FREEZE are also absent at that main ref, but remain exactly retrievable at their pinned source commit below.

## Source and manifest closure

[FREEZE.json](FREEZE.json) pins the candidate, runner, original independent auditor and three source/input objects. [FREEZE_AMENDMENT01.json](FREEZE_AMENDMENT01.json) preserves the original freeze and pins `independent_audit_v2.py` separately. All seven actual file SHA-256 values match these declarations. The amendment's original-auditor hash also equals the original freeze.

The three input objects were independently retrieved at pinned legacy commit [1675b2e3b3deb4ffbd2651098ccfc819aa53d123](https://github.com/Unjuno/agent-interface/commit/1675b2e3b3deb4ffbd2651098ccfc819aa53d123), at the exact paths in FREEZE. Their Git blobs and SHA-256 values equal the retained #5492 copies and #5489 copies above. There are three expected-inventory entries and three raw records.

Git history retains the corrected independent auditor at `0d22569f8ebf6720153f0d692797808af80fc0f5` and amendment at `9841736298c6ca14a7e4f0f42be43757ba408fd0`, before the stored RUN commit `9fb26133990271ea622127277e960267f5bfee80` and AUDIT commit `019115dcf8ce8576110414ec2fa731b146d11e1f`. This establishes repository publication order. The amendment's assertion that no earlier candidate/runner execution occurred remains a historical claim; publication order alone cannot authenticate it.

## Retained process records, without replay

[RUN.json](results/host-01/RUN.json) embeds 1,111 stdout bytes ending with the retained CRLF. Their exact SHA-256 is `a3a960e3007d008b6af01578780563e8aead5397f709280b514d99e7db74dbe5`, matching RUN and RESULT. Parsing those embedded bytes equals the separately stored `parsed` object exactly. The object records `candidate_missing_row`, `candidate_rejects_missing_row=true`, and the original host-only PASS alongside the other frozen decisions. All four source-hash values embedded in RUN match the corresponding retained inputs.

[AUDIT.json](results/host-01/AUDIT.json) embeds 303 stdout bytes, also retaining its CRLF, with exact SHA-256 `f36fcaf99919e13589287c005c3d9a67d230256665919974acc5ac65d25964c8`. Its parsed stdout equals the stored `parsed` object. It records eight checks true, including `missing_row_rejected` and `exact_decisions`, errors=[] and the original independent-audit PASS.

Both JSON envelopes record process exit 0. RUN records Windows CPython 3.11.9 and a host-only in-memory context. These are retained historical process claims, not processes observed by this review. The command files retain invocation templates, not fully expanded original argv; separate stderr and an external process-authentication record are absent. No omitted receipt or expanded command is reconstructed or invented.

## Independent-auditor boundary and safe integration

Despite its historical label, `independent_audit_v2.py` consumes the runner's decision JSON, rather than independently recomputing release identity from the raw fixture and expected inventory. Static inspection shows it checks decision lists, status/boolean fields and the set of source-hash keys; it does not itself verify the hash values or perform a second raw/inventory identity comparison. The value-level hash reconciliation above is a separate current static check. Preservation does not broaden the historical program into a general independent comparator or certify arbitrary-input correctness.

A minimal integration can add the 15 exact original blobs and this note to the chosen integration branch, then link this record as a separate complementary #5492 result. It must keep #5489's original FREEZE, sources and outputs unchanged and distinguish its candidate/run from this one. Any claim that the selected candidate satisfies the omitted-row acceptance gate requires its own reviewed equivalence rationale or separately authorized evidence; this preservation package does not supply that claim.

Do not rerun a consumed allocation, rewrite prior verdicts, normalize historical bytes, delete the source branch, substitute candidate identities or treat CI success as live-resource authorization. The package is evidence retention only; the reopened issue's final acceptance disposition remains explicit and separate.
