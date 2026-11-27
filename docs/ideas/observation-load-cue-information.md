# Observation load versus cue information

- **Status:** Scoped synthetic-method result; transfer unverified.
- **Source:** [Issue #8665](https://github.com/Unjuno/agent-interface/issues/8665), successor to #8651 and #6526; retained packet [PR #8700](https://github.com/Unjuno/agent-interface/pull/8700).
- **Idea:** Separate the effect of observation-system load from the informational content of a cue when a reactive policy chooses an action.
- **Outcome:** The preregistered finite CPU 2×2×2 fixture ran once: 256 attempts across four regimes, eight matched seeds, and all load × cue-content × response cells. Candidate and raw-only independent auditor each ran once; audit returned `PASS_METHOD_SCOPED`, zero errors, and rejected 5/5 frozen mutations. Designed contrasts were load-only −1.0, transient cue-content-by-response −0.5, stable control 0.0, and no-information control 0.0; classification was `MIXED_SCOPED_FIXTURE`.
- **Boundary:** This validates expected signatures in the authored deterministic fixture only. It does not measure GUI/OS scheduling, remote observation load, user tempo, safety, or product behavior. Preserve earlier A01–A04 outcomes and do not describe this as a live-interface result.
