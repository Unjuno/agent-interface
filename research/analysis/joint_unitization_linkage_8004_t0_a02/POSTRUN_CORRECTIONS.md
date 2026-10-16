# Post-run correction — A02 README latent-opportunity count

The frozen `README.md` says the two joint scenarios contain ten latent opportunities. That count is incorrect. The frozen auditor-only truth contains **11**: `e1`–`e6`, `e7b`, `e7c`, and `e8`–`e10`. The overlapping B and C records (`e7b`, `e7c`) are distinct latent events, as intended by the fixture. `audit.json` reports `latent_event_count: 11` for both joint scenarios.

This correction does not change the frozen source, candidate output, or formal disposition. It preserves the source typo and supplies the exact count supported by `auditor_truth.json` and the successful independent audit.
