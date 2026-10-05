# Issue #8084 A03 — can the A02 gate be estimated reliably?

**Disposition:** `STOP_AUDIT_INPUT_HANDOFF_PATH_ERROR`. T0 A03 was separately frozen from merged A02. Fixture generation yielded 6,000 rows; the single candidate call exited 0, but the single auditor call exited 1 because a host-side relative-path copy failed to put the raw candidate output in its isolated input directory. See [STOP.md](STOP.md); the raw output and failed auditor logs are retained and not re-used.

This allocation varies diagnostic sample size over `n={5,20,100}` for four stationary synthetic strata and 500 deterministic replicates per stratum/sample size (6,000 rows total). It preserves the A02 eligibility thresholds (`span >= 0.25`, `peak >= 0.70`) and assesses eligibility and top-pair selection variability. `candidate/` contains no latent rates, stratum labels, or scorer truth. `SCORING.json` and the binomial input generator are auditor/generation-side only.

See [PROTOCOL.md](PROTOCOL.md) for frozen H/T/D/C/U, thresholds, and isolation. A fresh successor allocation is being prepared with distinct seeds; A03 remains unchanged as a failed handoff record.
