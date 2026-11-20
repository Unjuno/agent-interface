# T1 A09 terminal STOP — duplicate claim IDs on first consolidation (2026-10-08)

**Disposition: `STOP_DUPLICATE_CLAIM_IDS`; no cadence result.** Candidate was stopped after its first consolidation, at row 30. The output expanded ep01 into five claims (action, context, exact_effect, kind, verification) all sharing id `ep01`, violating the frozen one-claim-per-episode transition contract. The frozen auditor was not invoked because the candidate was intentionally interrupted before completing the plan. Candidate had 36 recorded calls when the stop completed; no retry.

The generic prompt said to preserve every distinct fact but did not specify which fields make the canonical claim for each episode kind. A successor must map each input kind to one canonical output claim and ignore other metadata, while retaining the already frozen conflict-context and no-loss rules.

- Candidate: one invocation, exit 130, 36 recorded calls; auditor 0; retries 0.
- Raw: 199690 bytes, SHA-256 `872685b4010bcf8b67a12c6d19bf0303cb090daf8a6d26d009d4fa46d5915ed3`.

Do not resume or score this allocation.
