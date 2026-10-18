# Context-return renewal after cue–outcome reversal

- **Status:** Two consumed allocations failed their method/evidence gates; no behavioral result.
- **Source:** Issue [#8432](https://github.com/Unjuno/agent-interface/issues/8432), successor to [#8200](https://github.com/Unjuno/agent-interface/issues/8200).
- **Idea:** Test whether a previously useful cue–outcome response returns when an agent comes back to an earlier interface context after adapting to a reversal elsewhere.
- **Outcome:** A01's one candidate invocation wrote nine episodes (three per track) while stdout claimed 18; the independent auditor exited at an inconsistent 12-matched-episode gate. The retained disposition is `FAIL_METHOD`, not a behavioral verdict. A02 is a separate `STOP_RAW_NOT_RETAINED`: its sole OrbStack candidate invocation wrote raw output to container tmpfs, which was unavailable after exit; the auditor was not invoked and there was no retry or host fallback. Both outcomes remain immutable in merged [PR #8438](https://github.com/Unjuno/agent-interface/pull/8438) and [PR #8507](https://github.com/Unjuno/agent-interface/pull/8507). No model, GUI, or behavioral result is established.
