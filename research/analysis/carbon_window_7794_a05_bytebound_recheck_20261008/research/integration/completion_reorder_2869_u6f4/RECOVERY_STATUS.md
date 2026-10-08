# Current publication status — Issue #4306

This recovery preserves the exact source capsule for allocation
`completion-reorder-4306-20260924-u6f4-f01`. It does not repair or promote the
Issue-reported formal result.

## Source capsule verification

The original branch source capsule restored ten members with declared XZ
SHA-256 `39b86ced4906134e753cdcfdafb413a16acf8bf61810738c946c5104526f6488`;
the restorer reported `executed=false`. In Python 3.13.5, its excluded
contract tests passed 8/8 and six Python members syntax-compiled. These are
source-integrity and contract checks only, not the 24-session live allocation.

## Formal evidence disposition

Issue #4306 reports `PASS_COMPLETION_REORDER_LIVE_SCOPED` for 24 cases, but
the exact 20 evidence parts do not form a valid archive: their ordered
concatenation has 148,599 Base64 characters (length mod 4 = 3); strict
decoding fails, and adding padding diagnostically still produces corrupt XZ
data. No evidence manifest binds an archive/member inventory. No bytes were
repaired, guessed, or rerun during this recovery.

Therefore the PASS remains a historical Issue report and repository evidence
status is **HOLD_INVALID_FORMAL_EVIDENCE_CAPSULE**. The malformed parts are
intentionally not copied into this source-only main record; the original
branch commit and all its parts remain recoverable by the archive tag. Issue
#4306 remains open. No live/formal allocation was rerun.
