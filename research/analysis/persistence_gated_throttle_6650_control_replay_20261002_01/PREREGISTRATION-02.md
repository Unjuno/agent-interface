# Allocation 02 preregistration — Issue #6710

Allocation `PERSISTENCE-GATED-OPTIONAL-THROTTLE-6650-CONTROL-REPLAY-20261002-02`. This is a fresh one-shot audit allocation after allocation-01's pre-input harness STOP. Preserve allocation-01's exact source and `STOP_AUDITOR_FREEZE_KEY`; do not retry it.

Only the read-only freeze-key lookup is corrected: hashes now resolve under `FREEZE-02.json` → `inputs`. The fixture, predecessor RAW, independent event replayer, acceptance rule, nine mutations, container image/runtime/configuration and all thresholds remain unchanged. Candidate=0, independent auditor=1, retry=0.

The audit reads the immutable #6670 fixture and RAW, independently reconstructs 9×4 policy outputs, and must reject all nine preregistered corruption controls. PASS requires exact reconstruction and 9/9 controls; mismatch is `FAIL_AUDIT_REPLAY`; source/runtime failure is STOP/HOLD. No hypothesis retuning, original candidate run, or live task is allowed.
