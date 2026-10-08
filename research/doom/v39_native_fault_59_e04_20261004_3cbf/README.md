# E04 native fault/cancel successor evidence

**First formal outcome: STOP_RESULT_RETENTION_X11_CLOSE. Scientific PASS=false.**
Native1/official frozen auditor1/retries0/model0; both allocations consumed.
No RESULT/SUMMARY/AUDIT reconstruction or formal rerun is permitted.

Read REPORT.md for executed first failure, raw evidence and missing gates.
PRELAUNCH_STATUS.md/PRELAUNCH_REVIEW.md describe the historical zero-formal
preparation checkpoint, not current run counts. PROTOCOL.md/FREEZE.json and
all10 EXECUTION_PINS remain the actual unmodified pre-run source.

Raw native25files and independent docker-cp export25files are retained.
NATIVE_MANIFEST binds their exact inventory to retained-result commit
e6e8a0630b7645ce2b457bbbbc965fb519a2c613, with its own digest anchored in the
separate delivery verifier. DELIVERY_MANIFEST inventories delivery files;
late CI/review artifacts may require a refreshed inventory before final PR.

Construction/retention tests, delivery CI and verify_retention.py certify
method/failure retention only. They never execute runner.py or the consumed
official audit.py CLI, and cannot recover missing physical/reader snapshots.
test_partial_audit uses the NEW audit code on retained E03 data in private
temporary output to characterize partial-STOP behavior, never old allocations.

No production behavior is adopted. Actual useful gameplay, candidate native
fault behavior, model control, task effect, efficiency and full roadmap remain
open. A future separately frozen close-safe successor is required.
