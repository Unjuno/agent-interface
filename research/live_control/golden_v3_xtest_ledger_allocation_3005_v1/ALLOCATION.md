# XTEST emission ledger allocation #3005

Allocation: `golden-v3-identity-20260920-a2`
Docker image: `agent-interface-2994:20260920`
Image digest: `sha256:167fd6184cac8729ccfea407938943384d64fe2999e7319bed3587638fa94b7c`
Network: `none`

Instrumentation wrapped the additive Xlib XTEST call site and wrote one JSON line per fake_input request.

Observed:
- useful control: 35 XTEST requests, completed live GTK effect, verified release
- distinct-XID target replacement: 0 XTEST requests; focus verification failed before fake_input; raw runtime still reports failed-op effect as unknown
- source mismatch: 0 XTEST requests; `STALE_BINDING`, refused before backend execution
- decision: `HOLD_IDENTITY_FAIL_CLOSED_NOT_PROVEN`

The ledger is strong evidence that no XTEST fake_input call occurred in the replacement row, but it does not prove that all possible X11 side effects are absent. The uncertainty is retained exactly as a HOLD, not upgraded to PASS.

SHA-256:
- summary: `7c032f8c9f9d5d8d909bf2bc200cb499c5a6ab8cca19d3c3c8cfc23634d8d26d`
- useful XTEST ledger: `a766dc9868a0b6fddd9065884225b496b6f3f8e17ed8e12a77529004047c4ee2`
- instrumented backend: `6d42a2d69cf60527f58df7040f9eecebb163929dfff911353c645f6618a8c8f0`
- runner: `7a8822f88a39fd7c67f8396a97a2c0193c8e7966401c28ddc0644f375f75f218`
