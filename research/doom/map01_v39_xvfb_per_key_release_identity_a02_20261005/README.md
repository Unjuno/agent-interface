# MAP01 v39 Xvfb per-key release identity A02

This is a one-shot construction experiment for the current-main V4 backend and V3/V10 input owner. It checks per-key admission/release identity against real Xvfb client events, with repeated same-key cycles and a two-key reverse-order release.

The additive result-integrity correction in `results/RESULT_CORRECTION.md` records that 17 of 18 entries in the historical `results/RESULT_SHA256SUMS` verify against retained files. The listed `results/setup.log` (SHA-256 `dfdaa95b273e1714d9ddc76ff9138bf9dc4307c7588e023954d292ab359e62ea`) is absent from the committed result tree and transfer archive, so its bytes cannot be verified or recovered from this package. The historical manifest and original result are preserved unchanged. This missing setup log does not change the recorded A02 STOP outcome.

The previous A01 STOP is preserved. A02 uses OrbStack selective host mounts created with the isolated guest, so it does not rely on `orbctl push`. Its source is copied to the guest's local home; raw evidence is written through a separate mounted output path. `FREEZE.json` fixes current-main source hashes, preregistration, candidate, independent auditor, mutation tests, and runner before the guest run.

No Doom, model, GPU, physical input, game-time progression, threat exposure, useful feedback, bounded recovery, or MAP01 effect is exercised. This cannot satisfy Issue #59's live gates.
