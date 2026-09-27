# Independent-auditor attempt log

The formal matrix result was completed once and was not rerun. The following failures were confined to the separate read-only audit of that completed output; none modified `inputs/` or `results/`.

1. The frozen `independent_audit.py` raised `AssertionError: formal result case set mismatch`. Cause: its check compared a set of case names directly to the `EXPECTED_CASES` dict. It stopped before case-by-case audit. Preserved frozen script hash remains `45aeaa76971ae03ce2e29081a3c12013f92a834bd8ea5b76191c224444477e31`.
2. Independent-audit v2 container lacked `/work/raw_byte_audit.py`, required to verify the frozen candidate source manifest. No evidence rows were read.
3. The next v2 image also lacked `/work/independent_audit.py`, another candidate source explicitly listed in the source manifest. No evidence rows were read.
4. After source bundling was complete, the verifier rejected the original baseline because the verifier's expected-stage table incorrectly used `null`; the formal receipt correctly reports `structural_audit`.
5. After correcting that table, the verifier looked for the altered source under `cases/modified_source_bytes/sources/`; the runner stores this fixture at `cases/source_modified/sources/`. This stopped only the final mutation-copy assertion.

The v2 verifier and its Docker image were corrected without editing the frozen matrix, its inputs, any mutation copy, or the formal result. A fresh `--network none` container with the formal output mounted read-only independently verified all eight case receipts, byte-mutation construction, expected rejection stages, direct/CLI equality, and original/source hashes. Final outcome: `PASS_INDEPENDENT_RAW_BYTE_AUDIT`, zero errors. The earlier failures remain part of the record and are not relabeled as passing attempts.
