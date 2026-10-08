# Archival qualification: #4929 / source PR #4940

## Disposition and authority

This is archival preservation of the exact 13 files published at source PR
[#4940](https://github.com/Unjuno/agent-interface/pull/4940), head
`1a599d7e0e871ea6fb50766bd5f4080f2f385661`. All original files, including the
freeze, source, tests and reports, remain byte-for-byte unchanged. This separate
qualification and the parent-directory navigation entry are the only new prose.

**`HOLD_SOURCE_FREEZE_MISMATCH` remains the disposition.**
[Issue #4929](https://github.com/Unjuno/agent-interface/issues/4929) remains open.
Archiving does not establish construction PASS, a hypothesis conclusion, formal
seed authorization, or model/task/runtime/product promotion. The consumed
allocation must not be rerun; a corrected attempt needs a fresh successor
freeze/allocation. The predecessor #4908 / #4911
`STOP_CONSTRUCTION_OUTPUT_NOT_EMPTY` remains unchanged.

## What the retained evidence actually supports

- [REPORT.md](evidence/construction_boundary_01/REPORT.md) and
  [RUN_SOURCE_MANIFEST.json](evidence/construction_boundary_01/RUN_SOURCE_MANIFEST.json)
  report one local Docker zero-update construction-boundary invocation: 12 tests,
  9 passed, 3 failed, exit 1; zero optimizer steps, construction-seed runs, formal
  fits, or retries. Those are retained historical claims, not independently
  reproduced results of this archival work.
- The intended check was separation of launcher logs/receipts from a fresh,
  initially empty runner-output directory. The reported missing output/source
  fixtures triggered earlier fail-closed checks. Static reading of the retained
  launcher/tests is consistent with that explanation, but does not reproduce
  the invocation. Valid-binding log/output separation was not established.
- [RAW_TEST_OUTPUT.md](evidence/construction_boundary_01/RAW_TEST_OUTPUT.md) is
  explicitly a stdout/stderr **summary**, despite its filename. The 13-file
  inventory contains no original stdout/stderr capture or separate raw-only
  auditor result for this boundary invocation. The presence of auditor source
  files is not evidence that an independent audit ran.
- Formal seeds `9934211`, `9934311`, and `9934411` are reported as unspent. That
  statement does not authorize proceeding with this consumed allocation.
- The existing [Issue #4929 outcome checkpoint](https://github.com/Unjuno/agent-interface/issues/4929#issuecomment-5922685758)
  already discloses the reported 9/12 result, pre-run freeze mismatch, invalid
  fixture boundary, and no-rerun/no-promotion limits.

## Identity checks and unresolved historical metadata

Read-only retrieval and local byte hashing verified all 13 Git blob identities
and the original directory tree `b553ae083e0345d71de84ebfee74d6331ef198e6`.
Those checks establish which published bytes are preserved; they do not prove
which bytes were mounted or executed during the historical invocation.

All nine entries in the manifest's `source_github_blob_sha` match the preserved
inventory. Six of nine entries in [FREEZE.json](FREEZE.json) match; these three
freeze entries do not:

| File | Preserved FREEZE value | Preserved published Git blob |
|---|---|---|
| `test_construction.py` | `092461f57a30823fe36740d684c7d439936bf045` | `3737e7664d066f4d926ff92047b0248602846865` |
| `construction_launcher.py` | `79a914f99d210ca36078a420e7dc09ed94e367fa` | `090e29c75398395b68be9435562676c5f90e04c6` |
| `test_launcher_boundary.py` | `9f0633f04f3da1fa317744a9808b96b6932df876` | `ccba7d411de66eff872ee415cdd70941091be298` |

Seven of nine recorded `mounted_files_sha256` values match the corresponding
published bytes, comparing hexadecimal case-insensitively. These two do not:

| File | Preserved manifest mounted-file SHA-256 | SHA-256 of preserved published bytes |
|---|---|---|
| `construction_launcher.py` | `582D923227A00050FF8CB525682E691895466F7301F4E629DC72A2E0DDC8F211` | `9f5217b555c1ebb3587c863b0495bba28017a1f74671ef9dc9241329c10644a9` |
| `test_launcher_boundary.py` | `0D5B2FD9343DE87C9BF3FBB2773DC13B76BC8D607A5B7FA667E434F5BFD820BC` | `8658c33026428ab2750d0152071fe4ac1055bb162318674ec2ad277b4fc2c16e` |

The Git-blob inventory agreement therefore does not resolve the mounted-byte
binding. Neither the manifest nor the freeze is repaired or reinterpreted here.

Two further recorded differences remain visible:

- The freeze's `base_main_sha` and the boundary document's intake main are the
  39-character string `519f2c1bdb219697c2f5e92ae6c27714265d60e`; Issue #4929
  instead specifies `519f2c1bdb219697c2f5e92ae6c27714265d60e0`. The historical
  fields are retained as written, without treating the 39-character value as a
  verified full commit identity.
- [CONSTRUCTION_BOUNDARY.md](CONSTRUCTION_BOUNDARY.md) describes a 1-CPU limit,
  while the retained invocation command, report and resource record specify
  `--cpus=0.25`. Preservation does not reconcile that resource-description
  difference or certify the runtime/image/host claims.

## Archival verification boundary

Only repository metadata, file reads, static inspection, inventory comparison
and local byte/tree hashing were used to prepare this archive. No retained
source or tests were imported or executed; no Docker invocation, training,
formal run, retry, experiment, or independent raw-only audit was performed.
The scientific and operational limits above remain in force regardless of the
archive's publication status.
