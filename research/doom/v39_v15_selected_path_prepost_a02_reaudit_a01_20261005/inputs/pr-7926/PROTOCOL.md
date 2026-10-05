# A02 protocol: paired pre/post keymap sample in V39/V15 selected path

## H / T / D / C / U

**Hypothesis:** One sample before the first explicit UP and one after the release batch can classify each key while preserving the V39 `session_command` → V15 → release-batch backend v1 / owner V4-V3-V12 path and zero keymap queries between UPs. If SPACE KeyRelease is suppressed in the fake seam, only SPACE remains down at post-sample.

**Treatment:** Two cases in one candidate process, both admitting SPACE (65) and F8 (74), then releasing SPACE followed by F8: normal delivery; and one simulated lost SPACE KeyRelease. The pre sample is hooked immediately before the first owner `up` call. The post sample is hooked after the existing `input_state` owner sample. Per-key telemetry is annotated only after the post sample.

**Decision gate:** Require exact selected V15/backend v1/Executor v13 identities; pre sample `[65,74]`; two ordered UP attempts; zero `query_keymap` between UP attempts; normal post sample `[]`; lost-SPACE post sample `[65]`; per-row owner receipt identity and sample classification; normal cleanup with no keys down; partial cleanup failure retained with SPACE still down; all real-input/physical/application/authority claims false. Candidate runs once, then an independent raw-only auditor runs once only when JSON was emitted. Any mismatch remains FAIL/STOP; no retries.

**Comparison:** Same two-key batch without a lost KeyRelease versus the same batch with exactly one suppressed SPACE KeyRelease.

**Scope:** Current pinned V39 selector function and current V15 wrapper/backend/owner/executor sources; deterministic fake X display. V12 game-facing parent and DoomGame are stubbed. No real X11, physical key, full controller process/game loop, application effect, threat response, useful feedback, latency, bounded recovery, or gameplay is tested. XSync means server synchronization only. This synthetic result cannot authorize or substitute for the unassigned private live-game lane.

## Frozen invocation limits

Candidate invocations = 1. Auditor invocations = 1, contingent on parseable candidate JSON. Retries = 0. Do not rerun candidate or auditor after any result.
