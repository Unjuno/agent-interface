# Issue #8406 A02 — retained-raw audit result

## Disposition

`PASS_RETAINED_RAW_AUDIT_SCOPED`. The independent successor reconstructed and audited the exact retained A01 candidate bytes. A01's earlier `STOP_AUDITOR_KEYERROR_SCHEDULE_SHAPE` remains unchanged: A02 did not replace its output or rerun its candidate.

## Results

- Candidate invocations in A02: 0; auditor invocations: 1; retries: 0.
- Exact retained A01 raw SHA-256: `2c79a10fa6530d74ac17ea9c67816b9517c63235a4cd32fcf70a2d463d4d9f70`; pinned parent fixture SHA-256: `1c8b74dfdd8ec7c5a5950133709ae95e40cc687edb12ac128d66f696c79e54fb`.
- Independent full-object reconstruction: passed for 12 source episodes, source-content digests, all schedule updates, and all fixed-prefix visibility rows.
- Update counts: episodic-only 0, per-episode 12, batch-of-four 3, terminal 1.
- Query visibility: 16 rows per arm, 64 total.
- Hostile controls rejected: 5/5 (forged provenance, omit rare exception, collapse conflict as safe, mutate episode digest, misalign checkpoint).

## Limits

This is only a retained-data/parser and finite contract-integrity audit. It is not evidence that LLM memory contents change with schedule, that one cadence is superior, or that any GUI/task effect or policy is safe. No model outputs, actions, task effects, user data, or container isolation were involved. See `FREEZE.json` and `formal_01/RUN.json` for custody.
