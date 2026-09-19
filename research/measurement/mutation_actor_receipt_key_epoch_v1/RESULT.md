# Result — #1272 actor receipt key epoch

Decision: **PASS_MUTATION_ACTOR_RECEIPT_KEY_EPOCH_SCOPED**.

- 5 immutable batches ×48,000 =240,000 independent lifecycle traces.
- Candidate/oracle mismatches: 0.
- Retired-epoch SELF admissions: 0.
- Future-epoch SELF admissions: 0.
- Same-epoch replay SELF admissions: 0.
- Wrong-active-key SELF admissions: 0.
- Valid epoch1 and epoch2 receipts remain accepted.
- Same nonce value across different epochs is accepted only with independently valid signatures in the then-current epoch.
- Authority promotions: 0.
- Task-success promotions: 0.
- Batch reruns/replacements: 0.
- RESULT SHA-256: `cafe205ef1005711d0d8880560d9d0d73782a0b0968eeb7e0b3be547ba3d1137`.
- Batch concat SHA-256: `928b3c101736845160a0b600823905db6ad0682adbb458aacc0ec3a0679db1bb`.

A preformal large source transfer mismatch was detected before any formal row. The large bundle is explicitly non-authoritative; nine small authoritative chunks were verified 9/9 against local Git blob IDs before formal execution.

Scoped conclusion: binding authenticated SELF receipts to the runtime current key epoch closes the tested retired/future/wrong-key/replay path. Current-key compromise, secure key distribution, multi-host synchronization and authenticated real-human/kernel provenance remain open.
