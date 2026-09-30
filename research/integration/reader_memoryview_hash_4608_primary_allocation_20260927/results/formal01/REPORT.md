# Formal allocation 01 — FAIL

This report records the one authorized formal invocation for Issue #4608. The runner completed all scheduled workers, but the preregistered peak-allocation gates failed. This is a negative scoped result, not a candidate for reader adoption.

## Frozen conditions

- Local Docker image: `sha256:4c2cf9917bd1cbacc5e9b07320025bdb7cdf2df7b0ceaccb55e9dd7e30987419` (Linux/amd64, CPython 3.13.5).
- Docker restrictions: `--pull=never --network none --cpus=1 --memory=2g --pids-limit=64 --read-only`; only `/tmp` and the dedicated output mount were writable; frozen bundle mounted read-only.
- Source freeze: `a326861cf9a66dc5cf5b3229189e59c3e0ba11d1e06f2eda09551b2e5a69c8bc`.
- One runner invocation, no retries: 24 resource workers (4 cursors × 2 arms × 3 repetitions) and 2 untimed contract workers; all worker exit codes were zero.
- Runner RAW SHA-256: `d11b52ac74f90cc9418b267eacb111d92bc5d1581f7f396544fab0102d5b2da6`.

## Decision

Independent audit: `FAIL`, 166 checks, errors `peak_not_lower:2048`, `peak_ratio:2048`, `peak_not_lower:4064`, `peak_ratio:4064`.

| Cursor records | Baseline peak bytes (3 reps) | Candidate peak bytes (3 reps) | Median peak ratio | Median wall ratio | Median CPU ratio |
|---:|---|---|---:|---:|---:|
| 0 | 1,089,331 / 1,089,801 / 1,089,609 | 1,083,396 / 1,083,396 / 1,083,334 | 0.99424 | 1.07233 | 1.02159 |
| 2048 | 1,575,585 / 1,575,585 / 1,575,585 | 1,575,585 / 1,575,585 / 1,575,585 | 1.00000 | 0.87131 | 0.91705 |
| 4064 | 2,091,681 / 2,091,681 / 2,091,681 | 2,091,681 / 2,091,681 / 2,091,681 | 1.00000 | 1.01101 | 0.99753 |
| 4096 | 1,055,745 / 1,055,745 / 1,055,745 | 1,055,745 / 1,055,745 / 1,055,745 | 1.00000 | 1.06752 | 1.11376 |

Thus timing limits held in this allocation, but the required strict per-pair reduction and median peak ratio <=0.75 failed at both preregistered long-prefix cursors. At 2048 and 4064 the candidate did not lower peak traced allocation at all.

## Corruption controls

The post-formal ten-case corruption-control suite did not pass as a suite (`all_rejected=false`). Seven mutations (duplicate, source digest, result, input digest, exit code, corpus digest, and contract) were rejected with structured `FAIL` JSON and nonempty errors. Three mutations (drop row, arm, cursor) made the auditor raise `KeyError` on a missing pair; these had no structured audit error list and nonempty stderr. This demonstrates an audit-tool robustness defect; it does not change or invalidate the separately preserved formal outcome. The formal allocation was not rerun.

## Preserved evidence

`formal01-evidence.zip` contains the unchanged runner output, independent formal audit, and corruption-control output. Archive SHA-256: `91cebf75f5dab6e98cd69fc2eae960ddfc166a503fcca2ac2d571ecd24e4b955`.

Individual formal-output SHA-256 values:

| File | SHA-256 |
|---|---|
| `AUDIT.json` | `2e9dc4b0c25a2ab76cd7c251ce952208c27d88f0690ef1fb380ec1c70f73b880` |
| `corpus.jsonl` | `cf1f260335c010a36382254c275b6b0776f9b792c202a518302d101e4a9d3f26` |
| `CORRUPTIONS.json` | `b019777461aeed43f22d3e1fe678f08217a5c4b7d9700e6e6dc87d067c8e6fcb` |
| `INVOCATION.json` | `b7dab7849feed0f18bebed98fe1087a25f5eb61ed09c523f32bf8f7d276d1444` |
| `journal.jsonl` | `99ac68ab4aef7810b16cccd89cc6da46f79dbdd0e7897e8864c78672c115ec1` |
| `RAW.json` | `d11b52ac74f90cc9418b267eacb111d92bc5d1581f7f396544fab0102d5b2da6` |
| `RAW.jsonl` | `7327e5a1b59acce6b1b1321097b140eeff6b429119de22ae7adb2a6804f1185d` |

No source, threshold, result row, or predecessor artifact was changed after formal execution. The formal slot is consumed. Follow-up work, if any, must use a new successor allocation and address the measured zero benefit and auditor exception behavior without rewriting this record.

