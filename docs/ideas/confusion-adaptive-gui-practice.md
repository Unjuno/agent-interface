# Confusion-adaptive practice under heterogeneous GUI variants

- **Status:** Synthetic method work only; no participant or GUI transfer result.
- **Source:** Issue [#8084](https://github.com/Unjuno/agent-interface/issues/8084), successor to [#8080](https://github.com/Unjuno/agent-interface/issues/8080).
- **Idea:** Test whether learner-specific confusion estimates help order practice only when procedure variants differ in confusability, against blocked and random-interleaved schedules.
- **Outcome:** Preserve A03 STOP and A04 HOLD. A05 is a scoped synthetic method result; at n=20 its low-dispersion gate falsely activated in 376/1,000 trials. Merged [PR #8158](https://github.com/Unjuno/agent-interface/pull/8158) maps a finite overdispersion-gate frontier. Neither result establishes participant learning, GUI transfer, or benefit of adaptive practice. See merged [PR #8120](https://github.com/Unjuno/agent-interface/pull/8120).
