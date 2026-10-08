# #6030 S4 — audit-only recovery of the frozen S3 candidate output

Allocation: `VISUAL-EQUIV-5905-S4-20261001-AUDIT-01`  
Predecessor formal allocation: S3 `VISUAL-EQUIV-5905-S3-20261001-01`, STOP `STOP_AUDIT_INPUT_FORMAT / NOT_EVALUATED`.

S1, S2 and S3 remain immutable with their recorded STOPs. S4 does not rerun or replace the S3 candidate. It evaluates only the exact S3 raw output bytes whose SHA-256 is `FC900DC159087B6A07EABCDF5433E43F0CCBD8DF41EE31C2F8C3E74B81ABF4B0`, produced by the frozen candidate source `B2EB0050AE7DA78464C5F20617707D0160C77BB03EB14D437660C1CAAE29A95C` on the frozen observer input `4C485DDDEEFD206F3CF3676E7495CB9609FE9AB4EFF5B493DD83866D678B1470`. A format-aware independent auditor is a distinct successor allocation; it cannot make the failed S3 audit successful retroactively.

## H — hypothesis

The S3 candidate output is plain newline-delimited JSON while its observer input is gzip-compressed JSONL. A separately frozen auditor that opens `.gz` as gzip and `.jsonl` as UTF-8 text will parse both, independently recompute all 12 rows, and either return a scoped PASS/HOLD or fail closed on the first integrity discrepancy.

## T — bounded execution

- One auditor-only invocation over the exact frozen S3 `candidate.jsonl`, `observer_input.jsonl.gz`, and `truth.json` bytes.
- Zero candidate invocations in S4; no candidate source is imported by the auditor.
- Preserve S3 candidate stdout/stderr, raw JSONL bytes, source/input hashes, and its first audit STOP unchanged.
- Before source freeze, test only the parser's ability to load one tiny plain JSONL fixture and one tiny gzip JSONL fixture. These are construction checks and do not invoke the auditor over S3 candidate output.
- No retries, mutation-based re-audits, threshold edits, candidate reruns or relabeling. If the frozen audit CLI exits nonzero or its report gate fails, preserve `STOP_AUDIT_RECOVERY`.

## D — decision

- `PASS_AUDIT_ONLY_SCOPED`: one separate auditor invocation exits 0, emits the preregistered report, independently replays all 12 candidate rows, verifies six byte-identical observer pairs with distinct sidecar labels, and passes all four frozen corruption controls.
- `STOP_AUDIT_RECOVERY`: loader, parsing, report, identity, raw completeness or corruption-control gate fails. No scientific disposition is inferred.
- If the audit passes, report its contained scientific status exactly as scoped by S3; it remains a synthetic observational-equivalence boundary only.

## C — controls

The auditor reads truth only from the sidecar and independently reconstructs raster pixels, timestamps, cue values and input hashes without importing `candidate.py`. Construction tests exercise both file encodings. Formal output identity binds the exact S3 bytes by SHA-256. Existing candidate output is not edited.

## U — limits

This is an audit recovery over an existing synthetic candidate trace, not a fresh candidate experiment, prevalence estimate, live vision test, GUI/game run, safety result, product result or task-effect measurement. No Docker container/shared slot, network, model/provider, GPU or OS input is used.
