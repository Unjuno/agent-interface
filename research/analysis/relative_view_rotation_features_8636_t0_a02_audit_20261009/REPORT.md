# Issue #8636 A02 retained-raw audit-only result

**Disposition: `FAIL_AUDIT_ONLY_MISMATCH`; audit adjudication incomplete.** The sole audit invocation exited 1 on the third observation of the first oracle trial. It expected `STOP` at `0.015 rad`, while the retained event says `ACTION`. The freeze, raw archive, exact command, interpreter, and first traceback are preserved. No mutation controls or full reconstruction summary were reached. Candidate invocations=0; audit invocations=1; retries=0.

The observed mismatch is explained by a concrete auditor-policy error. The copied A02 runner calls the pose-reference action formula on every step before the step-12 limit; it has no `0.015 rad` STOP test for that arm (`source/runner.py`, frozen SHA-256 `71a6a68d…837cfd`). The audit-only implementation incorrectly applied `expected_oracle_action`'s image-arm tolerance to the oracle. This does not establish whether the other 2,572 event rows are correct. It is an audit implementation failure, not evidence of a scientific outcome.

The earlier A02 raw-only auditor also used the same `expected_oracle_action` tolerance rule, so its first `status does not match independent decision` is consistent with this defect, but the original traceback did not name the row. This is a source-based explanation of a plausible cause, not a retroactive reconstruction of the original first mismatch.

A02's original `HOLD_UNCERTAIN` remains unchanged: its auditor failed before a summary, and the formal `python3` invocation used Python 3.14.5 despite the freeze recording Python 3.12.13. This audit-only attempt cannot repair either fact. No rotation-feature hypothesis result, method PASS, real GUI applicability, task effect, safety, latency, or portability claim follows.
