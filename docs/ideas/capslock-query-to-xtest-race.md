# Caps Lock change between text guard and XTEST

- **Status:** Protocol draft only; no formal execution.
- **Source:** Issue [#8328](https://github.com/Unjuno/agent-interface/issues/8328), successor to [#8254](https://github.com/Unjuno/agent-interface/issues/8254).
- **Idea:** Test whether a deterministic Caps Lock transition after a per-text LockMask query but before the first XTEST event can change the emitted case despite the existing guard.
- **Outcome:** The exact A02 source identity readback passed, but the protocol remains `PROTOCOL_DRAFT_NOT_ALLOCATED`. No Xvfb preflight, public dispatch, or formal case ran; independent review remains unassigned. This is not evidence of a production race or authorization to alter shared runtime behavior. Open [PR #8338](https://github.com/Unjuno/agent-interface/pull/8338) records the current preparation state.
