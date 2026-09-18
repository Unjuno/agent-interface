# Result — #1290 actuation/effect receipt authenticity

Decision: **PASS_ACTUATION_EFFECT_RECEIPT_AUTHENTICITY_SCOPED**.

- 330,000 traces = 5 immutable batches × 66,000.
- Candidate / independent oracle mismatches: 0.
- Authenticated false self-credit: 0.
- Replay escape: 0.
- Unauthenticated bound baseline false self-credit: 90,000.
- SELF_EFFECT: 60,000; UNATTRIBUTED_EFFECT: 240,000; NO_EFFECT: 30,000.
- Authority promotions: 0.
- Batch reruns/replacements/tuning: 0.
- RESULT SHA-256: `908df46b5a7f1894229ff2f5243cd3f2c31b40a634d646fcb3dc1a6a11ebe2ec`.
- Batch concat SHA-256: `c98d142c0271e8c7321a94ada7d82a1a5833ea8512051d757b04113064c40842`.

Scoped conclusion: actuation_id binding is not trustworthy when an effect producer can self-assert those fields. Requiring an independent scorer-authenticated effect receipt plus nonce freshness rejects the tested unsigned, wrong-key, altered-field and replay paths while preserving valid signed self effects. This does not solve scorer-key compromise or establish live scorer isolation.
