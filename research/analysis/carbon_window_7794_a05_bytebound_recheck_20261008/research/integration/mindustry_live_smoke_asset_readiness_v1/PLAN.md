# Mindustry live-smoke asset readiness v1

Task `MINDUSTRY-LIVE-SMOKE-ASSET-READINESS-20260917-001`.

H: the current container already satisfies generic Linux/X11/Java/Python execution prerequisites, and the repository pin identifies the official Mindustry v160.2 desktop JAR exactly; the only remaining environment blocker is materialization of that JAR plus the retained canonical save.

T: source-first deterministic readiness gate. Compare frozen official-release metadata with the repository asset pin and retained canonical-save identity, then probe the current container for required executables/modules and candidate binary locations. No GUI/game/model/network task action. One formal invocation, zero reruns; independent auditor recomputes the disposition.

D: FAIL on provenance mismatch. HOLD_ENVIRONMENT_MISSING if generic execution prerequisites are missing. HOLD_ASSETS_NOT_MATERIALIZED if provenance/environment pass but either required binary is absent. PASS_ASSETS_READY only if both files are present and match frozen size/hash identities.

C/U: this does not run Mindustry or establish GUI/live correctness. A HOLD due binary absence is an environment/materialization result, not a scientific failure of the interface.
