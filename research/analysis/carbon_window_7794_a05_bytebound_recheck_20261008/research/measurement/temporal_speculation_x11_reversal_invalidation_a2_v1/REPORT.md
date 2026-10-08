# Result — #1215 A2 fresh-X11 reversal invalidation

Decision: **PASS_FRESH_REVERSAL_INVALIDATION_SCOPED**.

- detached formal runner invocation: 1; exit code0; reruns/replacements/tuning0
- predecessor #1204 rows pooled: 0
- reversal sessions detected before TTL: **20/20**
- continuation false invalidations: **0/10**
- capture exceptions: **0**
- reversal→YIELD latency: p50 **64.230 ms**, p95 **84.526 ms**, max **85.523 ms**
- stale-exposure reduction versus TTL_ONLY: median **89.970 ms**, min **88.211 ms**
- guard triggered on capture delta 0→50 ms in8 cases and50→100 ms in12 cases
- authority/input:0/0
- independent audit: PASS/errors[]; authored reversal-field leakage mutation rejected
- result SHA-256 `ef13f1869a9d55094d27235f3a7a0afde747f076cab21f1571a7128cd305d90e`
- source rehash exact; X11 process/socket cleanup0 remaining

Interpretation is scoped: #1194 showed reversal cannot be known before it occurs; this A2 result shows that after reversal becomes visible, a simple fresh-pixel direction guard can invalidate the stale continuation inside the frozen 20 Hz/200 ms envelope, substantially earlier than TTL-only and without false yields in these controls. It does not establish real-game/task usefulness or that 20 Hz is universally sufficient.
