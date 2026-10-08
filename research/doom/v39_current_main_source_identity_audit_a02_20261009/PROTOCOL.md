# #59 V39 current-main source-identity audit A02

## H / T / D / C / U

**H.** The r139 source identity cited by the retained Astra triage no longer identifies the top-level V39 controller on current main, even if the broad health/ammo validity and cancellation structure remains present. A fresh source identity check is required before reusing the old freeze for a new live allocation.

**T.** Read-only, standard-library static audit against one exact current-main commit. Compare top-level controller and V15 session hashes with the identities in `docs/CURRENT_GOAL.md` and `research/doom/MAP01_ASTRA_SYSTEM_FAILURE_TRIAGE_V1.md`, and compare them with historical tree `c1074c4dc385bae5b94ce93a5870e92c2e6ab07d`. Parse the controller, its imported `research/live_control/observable_signal_guard_v2.py` helper, and the V15 session. Report health/optional-ammo monitor inputs, frame-hash use, pending-wait monitor/cancel sites, and verified empty-release checks. Do not import, execute, patch, or simulate the controller.

**D.** `SOURCE_IDENTITY_MATCH` requires current-main controller and session hashes to match the retained r139 identities. A controller mismatch is `HOLD_SOURCE_IDENTITY_STALE` even if static guard structure remains present. Report static source facts separately. An unavailable commit/path, parse error, or missing required node is `HOLD_AUDIT_INPUT`.

**C.** The source change may be a compatible extension that leaves the relevant guard contract intact. Static inspection may miss dynamic behavior or external helper semantics; source growth alone does not imply regression.

**U.** This audit cannot establish runtime reachability, threat detection under game conditions, interruption timing, physical/per-key release, useful feedback, recovery, survival, progress, or task completion. It does not allocate the private game lane. No live game, GUI, model, input, or container is used.

## Frozen inputs and command

- Current-main source tree: `FREEZE.json`.
- Historical comparison tree: `c1074c4dc385bae5b94ce93a5870e92c2e6ab07d`.
- Retained expected controller SHA-256: `4548ca30b5a962946c7f81a58784a5b8e672a10635f4737c36b38f596b2c27ca`.
- Retained expected session SHA-256: `661b3ac311f72517670a8fe37bc2901e9479963af9cdb0a219ed83ea48601724`.
- One audit invocation, no retries: `python3 -B audit_current_main.py --main-sha <frozen-main-sha>`.
- This is a read-only source alignment review, not the live experiment required by Issue #59. A01's failed harness entrypoint remains preserved in its own package.
