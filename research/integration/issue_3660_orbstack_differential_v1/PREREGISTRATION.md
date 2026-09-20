# Issue #3660 — frozen-raw transition reconstruction

## H — hypothesis

A strict auditor implemented independently of the #3652 runner can reject re-sealed event reorder/extra-event mutations, operation-count mismatches (including bool-as-int), role-identity mutations, and cleanup-survivor mutations. Applied to the untouched #3652 formal-01 bytes, it will not promote the five transition claims to PASS where required receipts are absent; it will return a typed HOLD.

## T — one bounded experiment

- Input: exact #3652 formal-01 `result.json`, SHA-256 `f0df0248ff5e754a91e93271d9784f08d06ae1e8ff349b5f82f0fd015eb42883`.
- Source: #3652 frozen source commit `e8bd0f0dcb29dc194c1235f1f102db5e662dbed4`; original formal output and predecessor audit are read-only and unchanged.
- Runtime: existing OrbStack image `sha256:f8ae93cfedd412cfe39ca575a97abc32c4d6e99ee7b5cc7848e79e0ce08bdc9f`, `linux/arm64`, network disabled, read-only root, raw/source mounted read-only, result mount writable only for audit outputs. No app launch, GUI, input, model or formal allocation.
- Run the independent raw reconstruction and mutation suite once in that container. Mutants are copies, each independently re-sealed after alteration; preserve all exact mutant bytes and hashes.
- No retries, no rewrite of predecessor evidence, no formal GUI rerun.

## D — decision rules

- `PASS_MUTATION_CONTROLS`: untouched raw receives either a scoped PASS supported by all required receipts or a specific HOLD for missing receipts; every altered mutant is rejected as integrity failure.
- `FAIL_AUDIT_MUTATION_ACCEPTED`: any altered mutant is accepted as a valid reconstruction.
- `HOLD_AUDIT_EVIDENCE_INCOMPLETE`: untouched raw is structurally intact but the event-level third-input-operation receipt, modal owner/disappearance, Chromium generation-aware stale-admission, or fresh Calc return evidence is missing.
- `FAIL_AUDIT_INTEGRITY`: malformed protocol order/cardinality, event hashes, operation count, identity binding, or cleanup.

## C — controls and scope

The sole source is the exact historical raw. Mutation controls change only a copied JSON object and recompute event hashes where applicable. This tests audit sensitivity, not GUI correctness, task effect, or runtime admission behavior. The prior frozen allocation remains `HOLD_TASK_EFFECT_UNTESTED`; it is not rerun or reclassified.

## U — unknowns

The experiment cannot reconstruct observations never retained. In particular, a recorded `disposition: refused` is not proof that a generation-aware stale admission was invoked. No product/runtime or task-effect claim follows.
