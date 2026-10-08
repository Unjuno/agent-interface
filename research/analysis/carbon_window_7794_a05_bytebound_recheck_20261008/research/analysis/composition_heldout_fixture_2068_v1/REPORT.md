# Held-out composition fixture v1 — first result

Run: GitHub Actions `35443464575`
Commit: `5958b50612e4fcbbccbf804db7bb9934f87e4600`
Artifact: `10584980393`
Artifact digest: `sha256:fcdbc9f20da64cf1a3731ab7d525272e9d4769ed4214cb3a24858a7ccfd46754`
Result digest: `3618ac4aa6bf4405b5662fcbccaad9243b878e96f3918c16898198a4e0aa348d`

## Outcome

Decision: `PASS_COMPOSITION_FIXTURE_MECHANICS_SCOPED`.

- 10 controls × 3 arms = 30 rows.
- Formal invocations: 1; reruns: 0.
- Independent oracle: PASS.
- Unsafe emissions: 0.
- Stale target, missing provenance, UNKNOWN effect, and expired continuation stop in all arms.
- The composed correct case records cue use.
- The cue-ignored control is retained as `SUCCESS_CUE_UNUSED`, not counted as a composition benefit.
- Effect-verified/task-failed remains distinct from success.
- Retry, preflight, fallback, and skipped-stage fields are retained.

## Boundary

This is a deterministic standard-library fixture executed on Ubuntu 24.04. It does not establish model-facing behavior, real token/latency benefit, GUI/application effect correctness, DOOM transfer, or production safety. The fixture is a gate for the next held-out/live composition rung; #2068 remains open.

The artifact is immutable and expires 2026-10-19. No prior evidence was changed.
