# Current publication status — Issue #4161

This record accompanies the exact preformal `FREEZE.json` and `PREREG.md`
recovered from the owned branch. It does not change the allocation, its
reported outcome, or the separate c5d2 study merged in PR #4127.

## Recovered bytes and missing package

The audited branch head `26425fb588e02b704405da1a87b85a2b44147e5d` contains
only `FREEZE.json` and `PREREG.md` for this allocation. The freeze commits to
the exact source patch, fixtures, and a 30-case plan, but those source files,
raw rows, process receipts, and audit/control package were not present in the
branch or current `main`. Hash commitments do not reconstruct those bytes.

## Issue-reported outcome and disposition

Issue #4161 reports `PASS_RSS_INDEX_DENSITY_SCOPED`, 30/30 workers, a clean
raw-only audit, and 11/11 corruption controls. These remain historical Issue
reports only; they were not independently reproduced from the committed
package in this recovery. Repository publication remains
**HOLD_MISSING_SOURCE_RAW_AND_AUDIT** pending exact-byte recovery and
repository-only restore/re-audit. No experiment or raw audit was rerun.

Scope is limited to the stated Linux/CPython resident/private-memory fixture;
it is not a production sizing or leak claim. Issue #4161 remains open.
