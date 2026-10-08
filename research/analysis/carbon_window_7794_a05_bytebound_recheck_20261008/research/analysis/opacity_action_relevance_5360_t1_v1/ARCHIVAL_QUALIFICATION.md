# Archival qualification: #5360 T1 opacity construction history

Date: 2026-10-01. Preserve the 23 published package files from [PR #5408](https://github.com/Unjuno/agent-interface/pull/5408), exact source head [`443dbaa5142df2ac5b025d8fa9cb395bfd39f7be`](https://github.com/Unjuno/agent-interface/tree/443dbaa5142df2ac5b025d8fa9cb395bfd39f7be/research/analysis/opacity_action_relevance_5360_t1_v1).

## Disposition

**Historical deterministic host-construction evidence only. Formal/container invocations remain zero in the retained account; this archive neither completes the originally requested T1 container experiment nor renews its withdrawn/deferred resource request.**

The purpose is worker discovery and provenance preservation. All 23 original files, totaling 300,815 bytes, are retained byte-for-byte, including failed audits, repeated raw outputs, the explicitly named `audit-retry.json`, stale historical source hashes, and historical PASS language. [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json) identifies the original bytes. This qualification and the package README are additive. The old PR's shared `research/analysis/README.md` edit is not copied: only a fresh generated-index entry and an archival discovery link are proposed against the current main snapshot.

The latest retained matrix has 32 rows: eight declared lifecycle patterns × two read-use roles × two policies. It is an enumeration of that selected toy matrix, not an exhaustive proof over concurrent systems. Its recorded decisions show six invalid action-consumed histories: the weak comparator admits five; the opacity policy admits zero; both valid committed same-generation histories remain admitted. This is static inspection of existing data, not a new execution or independent reproduction of its scientific result.

## Owner, withdrawal, and current scope

- [Owner #5360](https://github.com/Unjuno/agent-interface/issues/5360) remains the hypothesis owner. Its T0 account, all 13 owner comments, and old draft PR remain history; archival navigation does not replace or close the owner.
- [T1 correction](https://github.com/Unjuno/agent-interface/issues/5360#issuecomment-5909422834) says the first mutation-coverage claim was too strong. [Attempt-07 correction](https://github.com/Unjuno/agent-interface/issues/5360#issuecomment-5909758256) records the scenario-label and rollback chronology defects. [Source/readback repair](https://github.com/Unjuno/agent-interface/issues/5360#issuecomment-5909849473) invalidates the earlier source binding at head `1e20c96c...`; the present archive does not silently validate it.
- [Queue deferral](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5913033567) explicitly defers the lower-priority #5360 request. The later [sole-lane clarification](https://github.com/Unjuno/agent-interface/issues/5085#issuecomment-5913301627) says #5360 and FEC/#5433 requests are deferred/withdrawn. Later unrelated queue entries mentioning a pending #5360 lane do not provide a named grant or reverse this disposition.
- Accordingly the historical PLAN/REPORT statements that a slot is requested or that the issue awaits its assigned runner are preserved as old statements, not current instructions. No active lease, exact assignment, or future run is created by archival integration.
- Governing guidance read at main snapshot `b2e7221c3c374cacc7037515f2df1508e965ac81` keeps component/construction evidence distinct from runtime success and keeps the broader r133 goal open. [Research method](../../../docs/RESEARCH_METHOD.md) permits finite analytical work within its assumptions and forbids promoting it to real-system evidence.
- The separate #5377 archive and #6027 publication are outside this packet; no files or claims from them are adopted here.

## Eight retained construction records

| Directory | Preserved contents and historical disposition |
|---|---|
| `construction-host-01` | Raw plus FAIL audit: action-relevance and generation mutation controls not detected |
| `construction-host-02` | Same raw bytes; FAIL audit: action-relevance mutation not detected |
| `construction-host-03` | Same raw bytes; historical PASS receipt, execution account, and old SHA256SUMS; later coverage correction retained in owner history |
| `construction-host-04` | Same raw bytes; FAIL audit: abort-status, action-relevance, and generation controls not detected |
| `construction-host-05` | Same raw bytes; historical corrected PASS account and SHA256SUMS; later found to depend on scenario labels |
| `construction-host-06` | Changed raw; only `audit-retry.json` is present as an audit receipt; later rejected as an adequate rollback discriminator because it consumed before commit |
| `construction-host-07` | Corrected raw with commit → consume → rollback; historical PASS receipt |
| `construction-host-08` | Audit-only successor, no new raw file; reuses attempt-07 raw by historical account; PASS receipt |

These are eight historical attempt directories, not eight independent successful experiments or eight container invocations. There are seven retained raw files and eight audit files. Raw attempts 01–05 are byte-identical, with SHA-256 `76af071d682818315d469edf808d45745b4225db758ac889ca18f8e8da225908`. All five PASS receipts (03, 05, 06 retry, 07, 08) are the same 48-byte JSON blob. Identical output does not prove identical source, controls, or execution.

## Byte and hash verification

The original files were read through GitHub at the exact source head. For every file, a separately calculated Git blob SHA-1 (`blob <length>\0<bytes>`) equals GitHub's returned identity. The manifest records those identities, byte lengths, and calculated SHA-256 values. No original output was regenerated, normalized, repaired, or replaced.

Verified current source and latest-output claims:

| File | SHA-256 |
|---|---|
| `PLAN.md` | `9e93f0fe6d7f0d157243d8e18e78bc03a7bdbcc0f6571c26b543e9122346d25d` |
| `simulate.py` | `0fb3cccb377a43d218c49d75fe1f7fe86c5508c09ea340ce8aae2350b5ed4549` |
| `audit.py` | `54253e2412225c59a6b7b410d5ec151facab357b3ee6d9fd77f73a128a6429b1` |
| Attempt-07 `raw.json` | `3fb5162d7f6e4d038e243068a829c024f7bf2b725f2d50cb39817b7ecc3fe30e` |
| Attempt-07 / attempt-08 `audit.json` | `6d3fbef7ef4b08a66c6ec97269cc12e53d3f5ad43635849c3a6110178968e452` |

The historical host-03 and host-05 SHA256SUMS each match their own raw, audit, and construction-account files. Their three root-source entries do **not** match the final package's PLAN/simulator/auditor: those files evolved. The final package contains only the latest root source versions. Earlier complete source snapshots are not bundled here, and the report's attempt-07 original-auditor hash `4e0e722e...` does not identify the final attempt-08 auditor. Preserve these as historical version claims; do not present the old checksum files as whole-package validation. This bounded archive does not retrieve additional old objects or repair the gap.

## Source and audit limits retained

Static reading of the latest source establishes these limits; no runner, auditor, test, mutation control, or source import was executed for this archive:

1. `FINAL_STATE_ONLY` checks only action epoch against final generation. It is an intentionally weak comparator, not an implementation of general final-state serializability.
2. The model has one identified read and one consumer/presentation event per row. The strict decision is derived from the complete history, including later abort/rollback events. An offline history classifier is not an online prevention or irreversible-action guarantee.
3. The latest auditor independently reconstructs cached projections and exact decision objects, but its general input validation is incomplete: sequence integers use `isinstance(..., int)` (which also accepts booleans), transaction identity and arbitrary event types are not comprehensively validated, and paired policies' underlying event histories are not explicitly required to match. Its expected matrix uses scenario labels without validating each label's entire event template.
4. The actual retained attempt-07 rows do have integer sequence values, exact 8×2×2 keys, and equal event lists for each policy pair. Those bounded observations do not turn the auditor into a general validator or add mutation coverage.
5. PASS receipts contain only `audit` and `errors`. They do not embed raw/source hashes, invocation identity, environment, or per-control output; raw files likewise lack a source identity. Historical execution/source attribution therefore depends on the surrounding account and commit history, not a self-binding receipt.
6. Attempt-06 retains `audit-retry.json`, not a complete initial-audit/retry transcript. The archive preserves that record and makes no exact total execution-count claim beyond the historical accounts. Attempt-08 has no new raw by design.

No production transaction manager, distributed concurrency, malicious-input robustness, irreversible effect, live runtime integration, model behavior, GUI/task effect, latency benefit, or user benefit is established.

## Intake, index, and CI boundary

The package is absent from refreshed main `5759a6e65b8b5e7487fb2ad61f53bb531aeaf512`: a direct package read returns not found, and the complete non-truncated `research/analysis` tree (6,635 entries; tree `05cd081e175031deed86a0e7dee9ec5ad06eb783`) contains no package prefix. The current generated index exactly covers 326 qualifying child directories. The proposed index derives the same set plus this package, 327 entries, using the current checker's template and codepoint sorting; surrounding content is preserved, with one additional archival discovery link. No historical shared-index blob is transplanted.

GitHub readback reports four successful old-head workflows: [Public Navigation](https://github.com/Unjuno/agent-interface/actions/runs/36709518479), [MAP01 replay gate](https://github.com/Unjuno/agent-interface/actions/runs/36709518314), [Research Workspace Index](https://github.com/Unjuno/agent-interface/actions/runs/36709518323), and [Analysis Index](https://github.com/Unjuno/agent-interface/actions/runs/36709518337). The complete all-events listing also contains two failed push-triggered runs on this exact source head: [MAP01 terminal-sync diagnostic](https://github.com/Unjuno/agent-interface/actions/runs/36709511401) and [mixed-app startup diagnostic](https://github.com/Unjuno/agent-interface/actions/runs/36709509756). Both jobs readbacks return `total_count: 0` and `jobs: []`. Their causes and any experiment execution are unknown; a failed workflow record with zero listed jobs is not evidence of a scientific run or a source-result failure. These same-head failures are preserved alongside the four successes, not described as only earlier-head history.

These are historical check records for the old head, not a newly run experiment or fresh archival-head CI. Earlier failures and corrections also remain in owner/workflow history. No historical check is inherited as a pass on a future archival commit, and this disclosure grants no retry permission.

Before any publication, independently review this qualification, all manifest identities, current-main absence, and the freshly derived index. Refresh the base and index if main changes; preserve the original package bytes. Publishing or merging this archive cannot authorize running its embedded commands, reopening a resource request, retrying an allocation, replacing a failed record, or promoting a scientific claim.
