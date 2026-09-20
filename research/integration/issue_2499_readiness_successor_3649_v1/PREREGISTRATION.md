# Issue #3649 — preregistration

Allocation: `issue2499-readiness-successor-3649-formal-01`.

- **H:** Using the bare `inkscape` command, already accepted by the pinned Inkscape 1.2.2 construction gate, allows the cookie-authenticated formal runner to resolve a unique Inkscape main window and proceed to the other two role identities. #3645's `Unknown option --no-splash` is retained as predecessor evidence.
- **T:** Freeze this additive source and pinned image provenance. Run unit tests, construction preflight with exact supported app commands, then one persistent mixed-app session in OrbStack/Docker with network disabled, read-only root/source, tmpfs only, and an independent audit that can validate both early STOP and full transitions. Exactly one formal invocation, no retries.
- **D:** Construction requires valid Xauthority cookie and three distinct exact-one role windows. Missing/ambiguous in-session role is typed STOP before geometry/input. Auditor validates any legitimate STOP/cleanup or all five transition checks; full transition gate PASS still yields overall HOLD because task effect is unscored.
- **C:** Same app versions, role filters, xauth cookie/Xvfb `-auth`, transition sequence, and model-free scope as #2499 v2/v4 and #3645; only fresh issue/allocation and the supported bare Inkscape command differ.
- **U:** No live model, user task effect, usage/cost, latency, human-tempo, broad GUI reliability, or product-release claim.

## Stop rule

Run only after frozen-source validation, unit tests, and cookie-authenticated construction preflight pass. Execute this formal allocation once. Preserve any result exactly; no tuning or rerun under this allocation.

## Stop rule

Run only after the unit and construction preflight pass. Execute the formal session once, no retries. Preserve any result or stop exactly; do not tune and rerun this allocation.
