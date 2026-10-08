# Issue #8135 T0 A01 — FAIL_INTEGRITY_AUDITOR_EXPECTED_SCHEMA

Formal allocation `UNJUNO-8135-T0-A01-ORBSTACK-20261005`, frozen on
`24cbb631b972eee1723d2372adf53032dfdaab20`. Candidate ran once and exited 0,
emitting 80 rows; the raw-only auditor ran once and exited 1 before writing an
audit JSON. Retries: 0. This is an auditor construction/schema failure, not a
scientific result about persistent counterparties.

Exact auditor stderr:

```text
ValueError: episode_field_set
```

The generated episode rows contain `arm`, but A01's independent auditor's
expected episode-key set omitted it. Candidate raw output, stdout/stderr,
`FORMAL_STARTED.json`, `RUN_RECORD.json`, source/input hashes, and the frozen
allocation remain unchanged. Do not rerun A01. A02 is a separate fresh-input
successor with the auditor schema corrected and a new schedule seed.
