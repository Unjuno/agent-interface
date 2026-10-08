# Result — #1295 scorer-key compromise boundary

Decision: **PASS_SINGLE_SCORER_ROOT_COMPROMISE_INSUFFICIENT_SCOPED**.

- 200,000 paired traces = 4 immutable batches × 50,000.
- Trusted legitimate receipt acceptance: 200,000/200,000.
- Current-key compromised receipt acceptance: 200,000/200,000.
- Verifier-visible byte-identical trusted/compromised pairs: 200,000/200,000.
- Wrong-key rejection: 200,000/200,000.
- Altered-after-sign rejection: 200,000/200,000.
- Authority promotions: 0.
- Batch reruns/replacements/tuning: 0.
- RESULT SHA-256: `4ba9622268219099d81f46038fd698f4685ed270a6ece5b04f3bcc0548464342`.
- Batch concat SHA-256: `9bdebfaf7de2e255814c1a42589f8b448a660cda3d3e0e6f889e05bcf2513717`.

Scoped conclusion: conditional on compromise of the current scorer HMAC key, a single scorer trust root is insufficient to distinguish trusted scorer provenance from compromised-signer provenance using the same receipt-visible evidence. This is a boundary result, not a repair and not an estimate of compromise probability.
