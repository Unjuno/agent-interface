# MAP01 v39 Xvfb per-key release identity A03

This is a one-shot construction experiment for the current-main V4 backend and V3/V10 input owner. It checks per-key admission/release identity against real Xvfb client events, with repeated same-key cycles and a two-key reverse-order release.

A01 and A02 STOPs are preserved. A03 corrects the Python-Xlib focus-call order exposed by A02 and requires a separate Xvfb focus readback smoke before its candidate. It uses OrbStack selective host mounts created with the isolated guest, so it does not rely on `orbctl push`. Its source is copied to the guest's local home; raw evidence is written through a separate mounted output path. `FREEZE.json` fixes current-main source hashes, preregistration, candidate, independent auditor, mutation tests, and runner before the guest run.

No Doom, model, GPU, physical input, game-time progression, threat exposure, useful feedback, bounded recovery, or MAP01 effect is exercised. This cannot satisfy Issue #59's live gates.
