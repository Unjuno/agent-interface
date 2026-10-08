# Issue #3834 formal-01 — terminal LF removal

## H / T / D / C / U

- **H:** Removing only the final LF from a completed JSONL CLI report leaves valid JSON that a parser-only caller accepts; a framing-aware caller detects incomplete delivery and recovers read-only without a second dispatch.
- **T:** One fresh current-main source freeze, one synthetic CLI allocation, five declared rows (full delivery, terminal-LF removal/recovery, invalid prefix, request-only unknown, occupied destination), and a separate raw-only auditor container.
- **D:** **`PASS_FRAMING_GUARD_SCOPED`**. The producer accepted 351 bytes and exited 0; the relay delivered the exact 350-byte strict prefix with only the terminal LF removed. Parser-only JSON parsing returned `valid_json` and the completed result payload, while the framing-aware check returned `false` for complete. The exact retained report was returned by real `attempt-status` and `review`, both exit 0; report SHA matched status evidence; snapshots were identical before/after recovery; synthetic dispatch count stayed exactly one. Independent auditor returned the same PASS with zero errors.
- **C:** OrbStack Docker 29.4.0 Linux/arm64, pinned Python 3.12 slim digest from `FREEZE.json`, network disabled, read-only root and source, separate fresh output mount, bytecode disabled. No model/provider, GUI, native input, external network, or production change.
- **U:** Synthetic local JSONL framing and retained-attempt recovery only. This is not real pipe/network truncation, live task recovery, power-loss durability, a broad reliability claim, or Docker Desktop/linux-amd64 parity. Does not close #3711/#3808.

## Raw evidence

- Formal runner stdout: `results/formal-01/runner_stdout.json`.
- Exact runner raw output: `results/formal-01/raw.json`, 7,801 bytes, SHA-256 `ff1a916ede722d07677977e942c72f8d7061e110e0cdbafb2e8cf09be68097ec`.
- Independent raw-only audit: `results/formal-01/audit.json`, five cases, zero errors.
- Accepted producer bytes: 351 bytes, SHA-256 `b027c295c619b525aa1ac1070c3a9b7a10fa754a7154c3ef44ecb89b51e5734a`.
- Delivered bytes: 350 bytes, SHA-256 `400e6dae93ce82dbf1815ac2ae9e2f9537bee92bbcf7e4affecdef950d3a4f02`; byte-for-byte `accepted[:-1]`.
- Persisted report SHA-256: `198c5a017a5d572c0202c11d4e852f224c2939c3840ba7670ae1fd199362009a`.
- Container source freeze revalidated 17/17 before both formal execution and independent audit.

## Reproduction

From repository root, set `OUT` to a new empty directory, run `validate_freeze.py` then `runner.py` once in the pinned network-none container with source mounted read-only and `OUT` separately writable. For the second container, mount `results/formal-01/raw.json` read-only and pipe it to `audit.py`. Exact reproducible invocations and their stdout are in `CONTAINER_RUN.md`; source and result digests are in `FREEZE.json` and `SHA256SUMS`.

All #3808 historical bytes and verdicts remain unchanged. The parser-only acceptance is the expected adversarial control, not the framing-aware caller's decision.
