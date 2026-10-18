# Internal versus environmental memory for GUI task sequences

- **Status:** Synthetic method result passed; task transfer remains unmeasured.
- **Source:** Issue [#8057](https://github.com/Unjuno/agent-interface/issues/8057).
- **Idea:** Compare internal memory with optional externalized environmental cues while accounting for stale/missing cues, collateral changes, restoration cost, and a separate safety floor.
- **Outcome:** T0 `PASS_METHOD_SCOPED` on a 12-case × four-arm finite fixture (96 rows) with independent candidate/auditor agreement and mutation checks. Environmental-cue arms failed the safety floor under planted warning-occlusion/restoration-failure cases; costs are authored toy units. No GUI, model, participant, token, or product result. Merged [PR #8095](https://github.com/Unjuno/agent-interface/pull/8095) retains the package.
