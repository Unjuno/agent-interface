# Issue #3645 — preregistration

Allocation: `issue2499-readiness-successor-3634-formal-01`.

- **H:** Explicitly creating an Xauthority cookie and passing the authority file to Xvfb with `-auth` allows the same frozen mixed-app runner to resolve unique Inkscape, Calc, and Chromium windows. The predecessor #3633 STOP is consistent with its empty authority file, but causality remains a hypothesis until this fresh allocation.
- **T:** Reuse the locally retained pinned image and source lineage from #3633, then freeze new source/image/provenance hashes. Run readiness unit tests and a construction-only cookie-authenticated Xvfb check first. At formal runtime use OrbStack/Docker, network disabled, read-only root/source, tmpfs only, and a single persistent session. Preserve ordered ledger and cleanup. Exactly one formal invocation, no retries.
- **D:** Construction requires the generated cookie to be accepted by the X server and three distinct exact-one role identities. In-session identity missing/ambiguous must be STOP before geometry/input. Auditor must distinguish a valid early STOP (only setup/stop/cleanup events, zero apps/input) from a complete five-check transition PASS. Overall successful session remains HOLD because task effect is unscored.
- **C:** Same app versions, role filters, transition sequence, and model-free scope as #2499 v2/v4 and #3633; only fresh allocation and explicit Xauthority cookie plus Xvfb `-auth` differ.
- **U:** No live model, user task effect, usage/cost, latency, human-tempo, broad GUI reliability, or product-release claim.

## Stop rule

Run only after frozen-source validation, unit tests, and cookie-authenticated construction preflight pass. Execute this formal allocation once. Preserve any result exactly; no tuning or rerun under this allocation.

## Stop rule

Run only after the unit and construction preflight pass. Execute the formal session once, no retries. Preserve any result or stop exactly; do not tune and rerun this allocation.
