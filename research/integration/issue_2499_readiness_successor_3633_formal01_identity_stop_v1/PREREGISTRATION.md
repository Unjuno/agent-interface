# Issue #3633 — preregistration

Allocation: `issue2499-readiness-successor-3633-formal-01`.

- **H:** The v4 role filters can resolve exactly one visible main surface for Inkscape, LibreOffice Calc, and Chromium; missing/ambiguous identity is typed STOP before geometry, transition, or input. With all three identities admitted, one persistent session can exercise focus drift, modal recovery, geometry change, Chromium replacement, and return-to-Calc without reusing stale identity.
- **T:** On the exact locally retained base image `mixed-app-identity-2782-local@sha256:e6ced3789130dae21c7b42b7b9d25cd590a271a77910e16c01d2edf87e44cee6`, derive a task image with Openbox/wmctrl and freeze the resulting image ID. Build/network is separate from the formal run. Use network-none and read-only-root/source at formal runtime; only `/tmp` and fresh evidence are writable. Unit tests inject one/missing/two identity candidates and ensure `geom(None)` cannot execute. Construction requires all three unique role matches and distinct identities. Then run the corrected existing model-free mixed-app runner once with bounded process waits and retain its ordered ledger/result and cleanup evidence. No retries.
- **D:** Identity gate PASS only if one candidate is accepted, zero is `STOP_IDENTITY_MISSING`, multiple is `STOP_IDENTITY_AMBIGUOUS`, and no missing/ambiguous identity reaches geometry/input. Session PASS only if every declared transition check passes in one process session and cleanup completes; otherwise preserve FAIL/STOP/HOLD. No PASS is attributed to the live agent adapter or task-effect scoring.
- **C:** Same three applications, transition sequence, role filters, and model-free status as #2499 v2/v4; only the source-bound unique-role resolver, explicit STOP boundary, isolated home/profile, and fresh successor allocation differ.
- **U:** No live model, user task effect, usage/cost, latency, human-tempo, broad GUI reliability, or product-release claim. This is a bounded desktop-session protocol gate only.

## Stop rule

Run only after the unit and construction preflight pass. Execute the formal session once, no retries. Preserve any result or stop exactly; do not tune and rerun this allocation.
