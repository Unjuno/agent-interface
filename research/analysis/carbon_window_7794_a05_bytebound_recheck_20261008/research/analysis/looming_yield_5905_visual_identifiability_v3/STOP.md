# S3 formal STOP: independent auditor input format

Issue: [#6030](https://github.com/Unjuno/agent-interface/issues/6030)  
Allocation: `VISUAL-EQUIV-5905-S3-20261001-01`  
Source: `6800d2e2a428e98d70cd35fd23dbda5343264dcf` (parent and frozen main: `722c42bf0d6d808cf80575ecb6353401de934b26`)

## Formal executions

The single candidate command exited 0 and wrote `candidate.jsonl` (4,542 bytes; SHA-256 `FC900DC159087B6A07EABCDF5433E43F0CCBD8DF41EE31C2F8C3E74B81ABF4B0`). Its stdout says `candidate complete: 12 records`. Candidate stdout/stderr and the exact invocation window are retained alongside this record.

The single independent auditor command exited 1. The frozen auditor's `load_jsonl()` unconditionally calls `gzip.open()` for both the compressed fixture and the candidate output. The candidate's preregistered output path is ordinary newline-delimited JSON (`.jsonl`), not gzip. It therefore raised `gzip.BadGzipFile: Not a gzipped file (b'{"')` before parsing any candidate row or writing `audit.json`. Full stderr and its hash are retained.

Disposition: **`STOP_AUDIT_INPUT_FORMAT` / `NOT_EVALUATED`**. Candidate completion is not a valid scientific result because the independent audit gate did not complete. No equivalence, cue-trigger, truth-separation, or scientific PASS/FAIL claim is made.

## Integrity / no-retry handling

- Candidate invocation count: 1; auditor invocation count: 1.
- No candidate rerun, auditor retry, source edit, patched-auditor replay, or result relabeling was performed.
- Preserve this freeze, raw candidate JSONL, stdout/stderr, and disposition unchanged. A future attempt must be a separately identified additive allocation whose frozen auditor explicitly accepts the distinct input/output encodings and tests that CLI path before formal launch.
- Preflight passed exact source readback and hashes, branch/base/parent equality, issue-open/scope check, empty output paths, and an empty main comparison path set at launch (`main=722c42bf0d6d808cf80575ecb6353401de934b26`).
- The run was host-only on Windows with Python 3.12.10 and the standard library. Docker Desktop's daemon was unresponsive, and no container or shared slot was used.

The experiment remains synthetic 64×64 monochrome raster construction. There is no live image-recognition, GUI, DOOM, safety, product, or task-effect claim.
