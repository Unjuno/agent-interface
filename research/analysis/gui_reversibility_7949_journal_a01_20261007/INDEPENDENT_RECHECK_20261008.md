# #8303 saved-SQLite recheck — 2026-10-08

## Disposition

The retained six-case result independently reconstructs from the committed
SQLite snapshots (`PASS_SAVED_DATA_RECONSTRUCTION`). This remains a synthetic,
finite protocol result only. It does not establish a production journal,
crash durability, concurrency behavior, GUI behavior, authority, or safety.

## Read-only checks

- All 30 entries in `results/SHA256SUMS.txt` match the committed files.
- The raw JSON SHA-256 is
  `7bacb35a06159c2f09dfae874eb9bba87b980f61857d76fdf36ce519e8d5a69f`,
  matching the report and retained audit JSON.
- An independent read-only SQLite reconstruction compared all six raw rows
  against their before/external/final snapshots, replayed external journal
  events, checked decision classes, compensation boundaries, and stale
  certificate labels: zero discrepancies.
- The retained audit states six cases and zero errors. No one-shot candidate
  or auditor runner was invoked during this recheck.

## Tests and environment stop

An initial local unittest attempt could not start: all eight tests stopped
before setup because Python could not create a temporary directory (`No space
left on device`). No candidate helper was invoked by that attempt. After free
space recovered, the same ordinary unit suite passed 8/8; these tests exercise
the candidate helper only in temporary SQLite fixtures and do not run the
formal candidate wrapper or one-shot auditor. Python compilation also passed
after space recovered. The earlier failure is an environment STOP, not a
scientific failure, and is retained here for chronology.

The original PR's two method-contract jobs were cancelled during checkout;
their Python setup and test steps were skipped. They are not test failures,
but provide no test evidence. Analysis-index checking on this sparse checkout
notes omitted sibling directories; workspace-index projection passed 162
top-level directories, and `git diff --check` passed. A full current-main CI
result is still required before integration.
