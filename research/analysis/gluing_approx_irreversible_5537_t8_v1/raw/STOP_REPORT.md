# T8 formal disposition — `STOP_AUDIT_MISMATCH`

- Allocation: `gluing-approx-irreversible-5537-t8-20261001-01`.
- Freeze base: `5a22b42f0d851d0d4549d197d37680d550b709df`; CPython 3.14.5/macOS arm64 host-only.
- Construction tests: 3/3; py_compile passed.
- Candidate command: `python3 -B run_experiment.py`, invoked once, exit 0, 135 rows; raw SHA-256 `810e143f44ed89f4f7b2481e631723eec37aed5413459d62425d80bf0ceb0b15`.
- Independent audit: `python3 -B audit_raw.py`, invoked once, exit 1, base_errors `[]`; only 2/6 mutation controls had valid non-identity changes and were rejected. Audit receipt SHA-256 `b89282733f99424f0039b07731629bf4b0c5857e9b0ec61b02e3070493c7f2c5`.

## Read-only diagnosis

The raw row schema merged fixture metadata and solver output at the same object level. This obscured the intended distinction between per-context evidence spread and declared fixture spread. Consequently several frozen mutation preconditions did not match the actual raw values; the audit harness correctly reported `precondition_and_nonidentity=false` and did not count those cases as tested. No candidate, auditor, raw, or audit edits/retries were made after the frozen invocations.

Because the preregistered six-control gate was not met, this is STOP, not PASS or scientific FAIL. Any continuation must use a new allocation and a nested, non-overlapping decision-input/output schema. T5–T8 remain unchanged.
