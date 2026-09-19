# Mixed-app persistent ledger allocation #2992

## Allocation A1

Ubuntu 24.04 arm64 image built with the PR Dockerfile. The package named `chromium` resolved only to an Ubuntu snap transitional package; no `chromium` executable existed in the container. The runner stopped at session setup with `FileNotFoundError`. This is retained as infrastructure STOP, not a mixed-app behavioral result.

## Allocation A2

Debian bookworm-slim image with real Chromium, Inkscape and LibreOffice:
- image digest: `sha256:766abfd10382ab8b59ed793094a685481190f840d338b7bc4664ca162a2da619`
- network: `none`
- one Xvfb session, fresh processes, no model/provider/network calls
- 15-event ledger, 3 input operations

Decision: `FAIL_MIXED_APP_LONG_SESSION`.

Observed:
- focus drift stale admission: passed
- modal transition/recovery: passed
- Chromium window replacement with distinct old/new window IDs: passed
- geometry transition: failed because LibreOffice geometry command returned empty old/new geometry
- return to earlier Calc active-window check: failed (`active` returned null)
- cleanup event recorded with neutral terminal input and no cleanup failure

The failure is retained as a bounded runner result. It does not claim broad GUI failure, and it is not upgraded to a PASS. The previous #2821 construction evidence and open PR #2992 remain unchanged.

SHA-256:
- result: `ab05a89d5336f4bad4b74f3c0fce5ae6d43696da5b3a74a8adaa7f5a03e23a5a`
- stderr: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- formal runner: `5668ee901f77ea2db356fcb29c3e76e6a0d839495ecc12bb202796daec59d4db`
- Dockerfile: `991df27493ee2490ccfc8a7975e834996e1af8451c92c5eaa6c6d03b4357d675`
