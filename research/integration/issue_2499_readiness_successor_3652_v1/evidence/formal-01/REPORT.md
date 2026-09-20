# Formal-01 result

- Issue/allocation: #3652, `issue2499-readiness-successor-3652-formal-01`.
- Formal disposition: `HOLD_TASK_EFFECT_UNTESTED`; scoped transition gate: `PASS_MIXED_APP_READINESS_TRANSITIONS_SCOPED`.
- All three role identities resolved READY (Inkscape, Calc, Chromium); all five preregistered checks passed; ordered ledger has 15 events.
- Formal invocation count 1, retries 0; model calls 0, network calls 0; 3 UI input operations were emitted for the modal and geometry transitions. Independent user-task effect remains unscored.
- Cleanup: no remaining process-group members; Xvfb socket removed. LibreOffice's top-level process returned code 255 at teardown; the audit accepts cleanup based on reconciled process groups/no survivors and preserves that return code in raw evidence.
- Chromium replacement reused the numeric XID (`identity_reused=true`) but had a new PID and surface generation 2 after the old window disappeared; stale-window admission was recorded as refused. Do not describe this as a fresh XID.
- Independent audit: `PASS_READINESS_TRANSITIONS_AUDITED`, 0 errors, 15 events.
- Frozen source commit: `e8bd0f0dcb29dc194c1235f1f102db5e662dbed4`; image `sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f` (`linux/arm64`).
- Raw result SHA-256: `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883`.
- Preflight SHA-256: `d67c27e3c3c850d6bebe79f524b5f24b5f746d3e8e74ad5ab4a0455fb8e6a658`.
- Audit SHA-256: `b8b2d3320e64ab8371e910b0f255298dd83ea265845d2fe15f4750244d8ce115`.

This is a bounded model-free readiness/transition protocol result, not an Agent Interface integration or task-effect result.
