# R09 result — NORMAL AND OPTIMIZED MODE PASS

## Outcomes

All four fresh-profile cases passed in both normal and `-O` Python.

- **Positive, each mode:** caller returned `TASK_SUCCEEDED` with
  `verified_effect`; local server recorded exactly one exact
  `value=t9910254` POST; independent scorer returned exact; both compiled
  admissions were `VALID`.
- **Changed generation, each mode:** caller returned
  `EXECUTION_INCOMPLETE` / `association_changed` after one completed action;
  second compiled admission was `SCOPE_MISMATCH` /
  `window_generation_changed_or_missing`; no submit dispatch, POST, or outer
  score occurred.
- All four case records have `profile_cleaned: true` and an empty cleanup
  error list. Post-run process/profile audit is in
  [`raw/cleanup-audit.json`](raw/cleanup-audit.json).

These are one positive and one refusal case per interpreter mode. The normal
and optimized runs verify behavior under those modes; they are not independent
reliability samples. A `ConnectionResetError` from a local HTTP server worker
appears in the optimized runner stdout during browser shutdown after the test
had passed. It did not change the exact POST, independent score, caller result,
or unittest exit 0. This shutdown log is retained for follow-up; it is not
silently discarded.

## Evidence

- Frozen conditions and source hashes: [`raw/normal/conditions.json`](raw/normal/conditions.json), [`raw/optimized/conditions.json`](raw/optimized/conditions.json).
- Case records, screenshots, OCR, handle admissions and receipts: [`raw/normal/`](raw/normal/), [`raw/optimized/`](raw/optimized/).
- Runner stdout and exits: [`raw/normal.stdout.txt`](raw/normal.stdout.txt), [`raw/normal.exit.txt`](raw/normal.exit.txt), [`raw/optimized.stdout.txt`](raw/optimized.stdout.txt), [`raw/optimized.exit.txt`](raw/optimized.exit.txt).

## Boundary

This is a first composed headless Edge/CDP fixture pass. It does not establish
physical OS input delivery or release, provider cost, repeated reliability,
Calc/MAP01 transfer, matched efficiency, or a distributable public runtime.
