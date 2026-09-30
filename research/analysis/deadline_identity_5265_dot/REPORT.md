# Admission deadline and effect identity: scoped analytical result

Related: Issue #5265; baseline PR #5338. See [PROOF.md](PROOF.md) for H/T/D/C/U and derivation, [REVIEW.md](REVIEW.md) for independent review, and [WITNESSES.json](WITNESSES.json) for six literal proof witnesses.

When deadline_ms means only proposal admission metadata, including it in semantic effect identity can split one supplied opportunity into two executions. Removing only that identity component gives the derived baseline/candidate counts 2/1, 1/1, 0/0, 2/2, 1/1, 2/2 across the six declared witnesses. Both retain the same strict deadline admission gate; meaningful effect delivery times remain in the payload.

These counts are analytical predictions, not observed experiment results. The predecessor explicitly included deadlines in its contract; its original result is not rewritten or reclassified as a failed test. No runtime implementation is changed.

Disposition: ANALYTICAL_COUNTEREXAMPLE_AND_CONDITIONAL_REPAIR_REVIEWED.
Runtime acceptance: HOLD_REAL_TARGET_BOUNDARY_UNTESTED.
Policy evaluations and experimental invocations: zero.

Identity, currentness, completion and sequential atomic effects are supplied assumptions. Real targets, concurrency, lost feedback, durability, latency and token benefits remain untested. Existing shared-work identity can encode the same repair; a new ledger is not established as necessary. Stored group deadlines are historical metadata, not a renewed lease or authority.

MANIFEST.json hashes all other retained files. Source copies are documentary inputs and were not imported or executed. PROVENANCE.json records source identities, preparation issues and actual host limitations.
