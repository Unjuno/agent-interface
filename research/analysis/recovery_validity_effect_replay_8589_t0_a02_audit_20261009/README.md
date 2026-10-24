# Issue #8589 A01 left-only gate audit

This additive audit-only package independently checks whether A01's retained complete `revision_left` schedule demonstrates the exact strict selective-versus-suffix recomputation advantage required by the frozen protocol. It also excludes the boolean-version alias from that decision. The A01 package is copied into `source/` as immutable audit input; no A01 file is modified or re-executed.

See `PROTOCOL.md`, `FREEZE.json`, and the single formal output `results/audit.json`. The conclusion is limited to the left-only decision-gate fact and does not revise A01's overall result or make any live-control claim.
