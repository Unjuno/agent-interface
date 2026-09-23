# Result — #1267 actor receipt authenticity A2

Decision: **PASS_MUTATION_ACTOR_RECEIPT_AUTHENTICITY_SCOPED**.

The predecessor #1263 consumed one monolithic formal invocation but produced no scientific output because the outer tool timed out. This fresh successor changed only outer orchestration.

- 12 immutable batches × 30,000 global IDs = 360,000 exact records.
- Coverage: [0, 360000), no gaps/overlap.
- Candidate/oracle mismatches: 0.
- Forged SELF admissions: 0.
- Replay attempts: 30,000; replay SELF admissions: 0.
- Valid signed SELF: 30,000 SELF_CONFIRMED.
- Explicit external: 30,000 EXTERNAL_CONFIRMED.
- NO_MUTATION: 30,000.
- UNATTRIBUTED: 300,000.
- Authority promotions: 0.
- Task-success promotions: 0.
- Batch reruns/replacements: 0.
- Independent aggregate audit: PASS.
- RESULT SHA-256: `70309055bcfbd226567ccc023f74357491b9291ec418267cf2f70734c4e60891`.
- Batch-concatenation SHA-256: `d0044f63aaba6aebeec58195e7719d1d11a08aaa0fcbf06260de594dd4379937`.

Scoped conclusion: runtime-bound HMAC-SHA256 receipts plus exactly-once nonce consumption close the tested forged/replayed SELF-receipt path in this synthetic contract. This does not solve key compromise, real-human/kernel provenance, or live-application receipt issuance.
