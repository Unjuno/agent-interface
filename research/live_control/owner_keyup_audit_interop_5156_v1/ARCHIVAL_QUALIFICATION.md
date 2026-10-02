# Archival qualification: owner-release audit interoperability

## Disposition and immutable origin

Preserve the complete 16-file package from [PR #5467](https://github.com/Unjuno/agent-interface/pull/5467), head `1675b2e3b3deb4ffbd2651098ccfc819aa53d123`, original directory tree `36da1b52d8044437520e6bc02aee60f597da6348`. Every original path, mode, blob, line ending, freeze, checksum and result is retained unchanged. In particular, results/construction-01/AUDIT.json and RUN.json retain their original CRLF bytes. This separate note adds qualification only.

This is archival delivery of a historical synthetic contract join. It is not a repaired auditor, new run, independently authenticated historical execution, formal X11 result or runtime promotion. The original PR was open/Draft at the 2026-10-01 review; [owner issue #5156](https://github.com/Unjuno/agent-interface/issues/5156) remains open. Original PRs and refs are retained; this archive does not ready or merge either source PR or clear a live gate.

## Historical result and failures retained

The [original result](RESULT.md) records `PASS_JOIN_CONSTRUCTION_SYNTHETIC_ONLY`, CPython 3.12.10 on Windows, 14 passing tests, one join-runner invocation producing three rows, and a subsequent separate completeness-only v2 audit returning PASS/errors=[]. The raw SHA-256 is `56842934b9f9b13fe0e52d515d31bd0c3d598cdb1cfa8b719dfb4c8ba463cbc2`. These are historical attributed records; no corresponding code was rerun for this archive.

The same result also retains the initial RED state: 13 tests errored while the join was unimplemented. The earlier [STOP_CROSS_PACKAGE_JOIN_UNIMPLEMENTED](https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5910424260) remains valid for direct owner-v1 rows, including rows augmented only with caller timestamps: schema, missing release_id and inventory errors remain. The later adapter is a separate construction, not a rewrite of that STOP.

Frozen inputs comprise two repeated same-key explicit releases, two distinct non-overlapping caller-v3 receipts, and an autonomous cleanup release. The normalizer assigns expected release IDs after identity/interval matching. Cleanup receives no fabricated caller interval. The inventory and source-shaped fixtures are synthetic; their presence does not establish actual owner emission completeness or an independent live admission/terminal inventory.

## Independent audit limitation and preserved failure

The independent `audit_join.py` calls the unchanged [#5415 completeness-v2 auditor](../owner_keyup_audit_completeness_5156_v2_20260930/ARCHIVAL_QUALIFICATION.md), blob `c37b6372f4e5a7306b98049c834559fdd60cadee`. The retained AUDIT.json explicitly says `caller_nesting_audited_here: false`. Caller pairing/nesting is checked by the adapter and its construction suite; the independent completeness auditor does not re-establish it from caller receipts.

The [independent source-PR review](https://github.com/Unjuno/agent-interface/pull/5467#issuecomment-5910884544) reports that both explicit-key corruption and cleanup null-to-string corruption are false-accepted with errors=[]. Static reading agrees that logical `key`, used by the normalizer and frozen inventory, is absent from v2's audited identity fields. The owner records [FAIL_RAW_AUDIT_MUTATION_COVERAGE](https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5910896174). Preserve this failure alongside the scoped construction PASS. It is not evidence that the original producer raw is itself corrupt, and no X11/scientific failure is inferred.

The [follow-up to #5553](https://github.com/Unjuno/agent-interface/pull/5467#issuecomment-5914793957) describes a separate logical-key correction. Main also preserves distinct #5489/#5492 key-identity candidates. None retroactively repairs this original auditor, transfers its own test count/PASS here, or independently authenticates this package's historical run. Byte matching and source reading cannot prove the claimed one-shot ordering, runtime, source mounting or process separation.

## Main coverage and exact-byte verification

At inspected main `d052c3a97086c236d7e65127b6076e0a3c39dec4`, all 16 original paths were absent. Main's separate #5489/#5492 namespaces already contained three exact shared input blobs:

- Baseline v2 auditor: `c37b6372f4e5a7306b98049c834559fdd60cadee`
- Expected inventory: `affa71e53457bb903353ce67b3477ef20b1d488c`
- Joined raw: `451247a5180348b8c29d09994dc0264f822585d1`

Those shared copies do not preserve the other 13 original files or this package's complete path/provenance relationships.

Archival preparation retrieved exact-head contents and complete nontruncated directory-tree metadata through GitHub MCP. All 16 reconstructed Git blob identities and 15 original SHA256SUMS entries matched, totaling 36,828 original bytes. The filename-first original SHA256SUMS format is preserved. Only static content, JSON, identity and checksum checks were performed. No retained source, test, runner, auditor, mutation control, X11/input, container or experiment was executed.

## Scope and owner boundaries

No physical key-up, X server key state, application consumption, held-input occupancy, MAP01/task effect, safety rate, useful-feedback timing, matched recovery, human tempo or cross-domain transfer follows. The [latest inspected #5156 scope/resource STOP](https://github.com/Unjuno/agent-interface/issues/5156#issuecomment-5926720911), A07 non-reuse, earlier failures and hypotheses remain unchanged.

[PR #5630](https://github.com/Unjuno/agent-interface/pull/5630), exact head `288d0498d11cf16657e523a04616bf4f49cd94f4`, is a separate active keymap/CLI package; [#5895](https://github.com/Unjuno/agent-interface/issues/5895) separately tests its completion-record semantics. Its [T6 owner-bound registration](https://github.com/Unjuno/agent-interface/issues/5895#issuecomment-5931175249) pins #5630 sources. This archive changes neither active branch/source nor allocation, experiment, raw, receipt, source freeze or authority. Recheck owner state before later publication/disposition; no slot, execution permission or gate clearance is inferred.

One combined archival PR carries #5415 and #5467, with separate qualifications and shared navigation only. The original frozen failures, records, source PRs and refs remain distinct.
