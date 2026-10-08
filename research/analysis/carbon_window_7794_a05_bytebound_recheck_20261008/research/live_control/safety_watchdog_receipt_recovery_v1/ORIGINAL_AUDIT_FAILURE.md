# Original frozen auditor failure

The frozen A2 scientific block completed all 8 first rows before audit.

The unchanged frozen `audit.py` then stopped post-measurement with:

`KeyError: 'journal_write_done_ns'`

at the journal ordering check. The journal persists the receipt before fsync completes, so the persisted row contains `journal_write_start_ns`; `journal_write_done_ns` is added to the watchdog's evaluator/debug receipt only after `fsync()` returns. The frozen auditor incorrectly read the done timestamp from the journal row.

No formal case was rerun, replaced, or modified. The exact aggregate remains the first outcome.
