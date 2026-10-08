# Issue #8596 T0 A02 — chance-bounded progress under delay uncertainty

This CPU-only finite-model experiment tests whether a deadline probability bound can say something useful when no all-traces finite progress guarantee exists, while retaining an independent hard-safety gate. It compares exact interval-probability bounds with a deliberately naive midpoint estimate, two authored delay distributions having the same mean, a rare disturbance with adversarial consequences, and an unidentifiable model.

The experiment invokes no GUI, OS input, model, external service, GPU, shared VM, or runtime action. Probabilities and the illustrative 0.8 threshold are authored fixture values, not estimates or task requirements. Read `PROTOCOL.md`, `FREEZE.json`, and `REPORT.md` together. Raw candidate and audit outputs plus command receipts are in `results/first-outcome/`.

The result is limited to exact arithmetic on these finite synthetic models. It does not calibrate real delays or establish task progress, safety, latency, human-tempo, or product behavior.
