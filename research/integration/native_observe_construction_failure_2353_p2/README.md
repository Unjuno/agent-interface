# Native observe construction-failure successor (Issue #2353 review P2)

This additive test closes the observation API boundary identified in PR #2353: backend selection may succeed while native backend construction raises a `RuntimeError` (for example, X11 capability setup failure). The API now returns a structured `observation_failed` row instead of raising a traceback.

Scope is deterministic source/unit behavior only. No GUI, X11, model, network, input, task effect, or authority is used. The test also preserves the existing `backend_unavailable` distinction and verifies a normal read-only result.
