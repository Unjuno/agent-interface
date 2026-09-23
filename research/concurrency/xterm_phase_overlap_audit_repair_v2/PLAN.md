# #1710 audit-only successor to retained #1707 FAIL

H: the 12 original serial_order failures are entirely caused by selecting the last done|done_already diagnostic rather than the first terminal transition. Re-evaluating the exact predecessor raw ledger with first-terminal semantics will satisfy every original scientific gate.
T: no X11/XTEST/task input. Pin predecessor raw/result/audit/schedule hashes, freeze one independent standard-library auditor, invoke once.
D: PASS_REAL_XTERM_PHASE_OVERLAP_AUDIT_REPAIR_SCOPED iff predecessor hashes and original FAIL signature match exactly, all 24 original correctness/order/tail/neutrality/performance gates pass, corrected errors=0, audit invocation1/reruns0/tuning0.
C: another gate may fail after the timestamp fix; then retain FAIL and do not rerun XTerm.
U: audit repair can validate only existing #1707 evidence; no new samples or broader performance claim.
