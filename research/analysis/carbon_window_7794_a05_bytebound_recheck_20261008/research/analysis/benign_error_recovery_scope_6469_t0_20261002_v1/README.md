# Issue #6469 T0 — benign-error recovery-scope trace assay

This is the Issue's first, low-cost **measurement-method** rung: 6 synthetic trace families × matched error/no-error conditions × 4 policy-recording arms = 48 assigned rows. It records `PROPOSE → ATTEMPT → GATE → SYNTHETIC_EFFECT → DISCLOSURE` separately, alongside task success and STOP, using a frozen exact-operation envelope and an independent raw-only auditor.

All traces are stipulated fixtures. “Synthetic effect” is a row in a test corpus, not an executed GUI/tool action. No model, human, external system, credential, live authorization, or real effect is involved. A T0 PASS can validate only measurement reconstruction; it cannot establish error-triggered behavior in any agent, reduce realized harm, or transfer the external paper's rollout rate to this repository.

The requested formal candidate and independent auditor run once each in separate network-disabled OrbStack containers with a digest-pinned Python image, read-only input and a distinct bounded writable output directory. See `FREEZE.json`, `RUN.json`, `REPORT.md`, and `SHA256SUMS` for exact provenance.
