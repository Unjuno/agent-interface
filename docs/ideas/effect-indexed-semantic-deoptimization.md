# Effect-indexed semantic deoptimization — #8040

- **Status:** Finite-method result; runtime and GUI transfer remain unverified.
- **Source:** [Issue #8040](https://github.com/Unjuno/agent-interface/issues/8040), successor to [#4260](https://github.com/Unjuno/agent-interface/issues/4260); retained evidence is in [Draft PR #8062](https://github.com/Unjuno/agent-interface/pull/8062).
- **Idea:** Map a specialized macro's declared safepoints to generic semantic-operation cursors while preserving independent effect evidence. Resume past only VERIFIED effects; yield on UNKNOWN, stale generation, or incomplete mapping. The map must not create action authority or retry permission.
- **Outcome:** T0 A01 reports `PASS_METHOD_SCOPED`: one candidate and one raw-only auditor reconstructed all 12 frozen rows with zero errors and rejected 6/6 mutations. In the authored fixture, the map advanced two verified-prefix cases to later generic cursors; this is not an observed GUI replay reduction. The report remains in a Draft PR rather than integrated main evidence.

## Boundary and next question

This method tests finite state reconstruction, not whether a real GUI effect receipt is trustworthy, a map is complete, or a live interruption is resumable. The formal run used native macOS because OrbStack image inspection stopped on a container content error; it establishes no container or OS-isolation result. A later transfer would need a separately owned disposable application fixture and independent effect oracle. If the effect state is UNKNOWN, preserve yield/stop rather than replaying or continuing.
