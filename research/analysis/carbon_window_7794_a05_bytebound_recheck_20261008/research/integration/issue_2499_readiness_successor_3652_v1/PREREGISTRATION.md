# Issue #3652 — preregistration

Allocation: `issue2499-readiness-successor-3652-formal-01`.

- **H:** Removing LibreOffice `--nodefault` while retaining its isolated profile and `--calc` yields a visible Calc main window accepted by the preregistered role filter. Construction diagnosis without `--nodefault` showed `Untitled 1 - LibreOffice Calc`; the formal run with the flag showed no such window. These observations motivate but do not replace this fresh, frozen test.
- **T:** Freeze this additive source and pinned image provenance. Run unit tests and the exact modified app construction preflight, then one persistent mixed-app session in OrbStack/Docker with network disabled, read-only root/source, tmpfs only, and independent audit for early STOP or complete transition set. Exactly one formal invocation, no retries.
- **D:** Construction requires valid Xauthority cookie and three distinct exact-one role windows using the Calc command without `--nodefault`. Missing/ambiguous in-session role is typed STOP before geometry/input. Auditor validates STOP/cleanup or all five transition checks; transition PASS still yields overall HOLD because task effect is unscored.
- **C:** Same app versions, role filters, xauth cookie/Xvfb `-auth`, transition sequence, and model-free scope as #2499 v2/v4 and #3649; only fresh allocation and removal of Calc `--nodefault` differ.
- **U:** No live model, user task effect, usage/cost, latency, human-tempo, broad GUI reliability, or product-release claim.

## Stop rule

Run only after frozen-source validation, unit tests, and cookie-authenticated construction preflight pass. Execute this formal allocation once. Preserve any result exactly; no tuning or rerun under this allocation.

## Stop rule

Run only after the unit and construction preflight pass. Execute the formal session once, no retries. Preserve any result or stop exactly; do not tune and rerun this allocation.
