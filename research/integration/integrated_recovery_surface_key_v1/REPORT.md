# Integrated recovery surface key v1 — readiness HOLD

Decision: **`HOLD_PREDECESSOR_IDENTITY_INCOMPLETE`**.

The preregistered 64-row validator comparison was **not run**: formal rows 0, formal invocations 0, reruns 0.

Both exact predecessor archives were materialized and SHA-verified before inspection:
- #855 / PR #860: Git blob `d345cb087d77c197a85b5f652abbf5052a55b80f`, 10,012 bytes, SHA-256 `46f08082f3bd58ed67b9a8a16d3fe26c10774d6d7ead246202a10c40e724e9ae`;
- #861 / PR #864: Git blob `bcf8203d54907cea5676d8143783dd249e6dda3c`, 10,652 bytes, SHA-256 `5c7725f878028e620a4edf975fe890b0b2d8fda0071cd286a3c70163ca4d96d6`.

All 16 retained cases contain exact top-level `client_id` values. The #864 modal cohort also records `transient_for` for source/current contexts in all 8 cases. The older #855 cross-app cohort records **no `transient_for` field** for either source Inkscape or current XTerm in all 8 cases.

Issue #873 froze a single key `{backend:x11, top_level_client_id, transient_for_or_null}`. Mapping the absent #855 field to `null` would convert unavailable historical evidence into an observed no-transient fact. That is forbidden by the experiment contract, so the unified-key efficacy matrix stops before formal rather than silently changing the key or inventing evidence.

This does not weaken #855, #864 or #865. Their scoped results remain valid. It identifies a historical evidence-schema boundary for cross-cohort generalization. A future fresh XTerm transfer can close it by retaining the same top-level/transient fields as the modal cohort; active #862 already owns the relevant live persistent-client/XTerm lane, so this branch does not duplicate that experiment.

Local readiness source SHA-256: `1d0d8cfa0a11c6bf9324720ebf2ec94cea8e1ffdf839ac0bc5f1619c9dc5fef0`. Compact readiness result SHA-256: `e37ab41880217cedf7e9d70c809569dafa0e575d7bf261234e65229d1fe43a0d`.
