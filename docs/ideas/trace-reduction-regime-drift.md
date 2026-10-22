# Trace-reduction guarantees under temporal regime drift

- **Status:** Finite method result passed; transfer beyond the authored model is unverified.
- **Source:** Issue [#8493](https://github.com/Unjuno/agent-interface/issues/8493), successor to [#8152](https://github.com/Unjuno/agent-interface/issues/8152).
- **Idea:** Compare pooled stationary confirmation with block-conditional confirmation to see whether pooled non-inferiority can hide target-fingerprint recurrence loss after a within-instance temporal regime change.
- **Outcome:** Frozen A01 `PASS_METHOD_SCOPED`: pooled confirmation accepted both planted harmful-shift cases; block-conditional confirmation rejected both. Stable controls passed, sparse and transition-ambiguous cases returned UNKNOWN, and competitor fingerprints remained distinct. Independent audit reconstructed 6,424 rows and rejected 6/6 corruptions. No real-system nonstationarity or runtime guarantee follows. Open [PR #8819](https://github.com/Unjuno/agent-interface/pull/8819) preserves the result package.
