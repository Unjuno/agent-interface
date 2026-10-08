# Issue #3595 auditor prechecks

These are construction-stage checks only. The three formal #3587 bundles were
not read by the v2 auditor before its hash freeze.

- Syntax compile: passed under host Python 3.14.5.
- The first two test invocations targeted an already-existing bind/output
  directory, so the auditor correctly refused `exist_ok=False` before reading
  evidence. No audit was performed by those invocations. Subsequent commands
  used a new child output directory.
- The first construction-bundle audit identified a bad filename-equality
  assumption: MCP presentation copies a capture to a new filename while the
  retained API receipt points at the separately named native capture. The v2
  auditor was corrected to bind the two files by bytes and SHA-256, not by
  generated basename. The original #3587 runner/auditor/raw data were not
  modified.
- Final precheck on the one excluded construction allocation: its per-row
  reconstruction passed with zero failed checks; all 10/10 in-memory
  corruption challenges were rejected. Overall output was deliberately
  `HOLD_OR_FAIL` because the test input contained one construction allocation,
  not the frozen required three formal allocations. No formal #3587 input was
  read in the precheck.

