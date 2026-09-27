# W2 Draft 2020-12 schema audit result — 2026-09-28

## Disposition

**PASS_DRAFT2020_12_METASCHEMA_AND_TRACE_CONFORMANCE_SCOPED**, independently rechecked. The result is additive to PR #4904 and Issue #60; it does not alter or upgrade the original W2 result.

## H/T/D/C/U

- **H:** Exact W2 schema is a valid Draft 2020-12 schema and its eight frozen trace examples conform under an independent standards implementation.
- **T:** Current-main snapshot at source readback `04564ff4d1df59f01a91de7338c44adab9ae74ab`. Input blob IDs remained identical at this main: schema `ebc424d2df631aa74c6d9aee4699c595a27ed589`; cases `0a49a00567c25766495cd332be50f6c2946781f7`. Docker Desktop image `python:3.12-slim`, ID `sha256:2f17fc044b579bab302c2e8054d3a686e2cb9a83de48e70534b94cd8ebbe06a9`, linux/amd64, Python 3.12.14. Used jsonschema 4.25.1 and five pinned dependencies, installed offline from a read-only wheelhouse. Network disabled; root/source/wheelhouse read-only; 0.25 CPU, 256 MiB, 32 PIDs, dropped caps, no-new-privileges; `/tmp` tmpfs explicitly `exec`; output-only writable bind.
- **D:** `Draft202012Validator.check_schema`: PASS. Frozen trace cases: 8/8 valid. Seven deliberately malformed schemas: 7/7 rejected by the Draft 2020-12 meta-schema. Seven malformed instances: 7/7 rejected. Source SHA-256 matched frozen inputs. Separate second container independently reran meta-schema and 8 instance checks, reconciled the exact candidate-result hash and reported `PASS_INDEPENDENT_DRAFT2020_12_RECHECK_SCOPED`.
- **C:** This confirms JSON Schema dialect validity and shape/instance constraints for eight synthetic cases. The separate W2 custom verifier/auditor remains responsible for its cross-event interval, lease, authority, event-order and numeric invariants. The independent recheck recorded the mutation counts from the candidate result; the original candidate executed each mutation directly.
- **U:** Does not calibrate clocks, establish physical input occupancy or useful live task effect, test recovery efficacy, resolve Worker returns or inherited leases, close Gate 1, or authorize W3/W4/formal work.

## Container sequence and raw outcomes

1. Allocation 01 — STOP before validator execution: wheels installed, but native `rpds` extension failed to map from `/tmp/site`. Exact retained diagnostic in `STOP_01.md`; no schema checks ran.
2. Allocation 02 — STOP before validator execution: PowerShell-to-`sh -c` quoting produced `Unterminated quoted string`. Exact retained diagnostic in `STOP_02.md`; results-v2 stayed empty.
3. Disposable v3 dependency-loader preflight — PASS: same pinned image/wheels/limits with explicit `/tmp:rw,exec`; imported jsonschema 4.25.1 and rpds successfully; no schema audit invoked.
4. Allocation 03 candidate audit — exit 0. Raw JSON is `results-v3/audit.json`; stdout/stderr and pip logs retained beside it. Candidate stderr contains the literal `SystemExit: 0` because the script's top-level exception logger catches normal `SystemExit(0)`; subprocess return code remained 0 and the result JSON is complete. This output blemish is disclosed, not suppressed or interpreted as a validation failure.
5. Independent audit — separate container, exit 0, stderr empty; rechecked source hashes, standards meta-validation and all eight trace instances without importing `meta_audit.py`.

All allocations/preflight/audit invocations: formal=0, model=0, GUI=0, game=0, physical input=0. Docker was idle after both runs.

## Primary result hashes

- Candidate `audit.json`: SHA-256 `f0ed5c65f09dba67ba78ead385301099ca19924d5b3cab82ff7d10219cf041b9`.
- Independent `independent-audit.json`: SHA-256 `88fac8b6fe786942b0a9467feeae2878f3a12780db45c66ab4595b4e0e90b094`.
- Candidate stdout: `45375d1e66e42a741d858f74358471e8827ee5fadec36c0991907002dee65a47`.
- Candidate stderr: `bff5ac03835e0cd2c4d58d875c39ca71cd941b61f8e00daf5d4d400013b61e26` (14 bytes: `SystemExit: 0`).
- Independent audit JSON and all run-log hashes are enumerated in `HASHES.txt`.

The exact commands, source/auditor hashes, wheel identities, preflight receipt, raw JSON and independent report are retained in this additive output directory. No retained W2 or MAP01 outcome was recomputed or rewritten.
