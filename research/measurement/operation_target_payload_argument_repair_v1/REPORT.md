# #1212 payload-argument normalizer repair — first outcome

Task `OPERATION-TARGET-PAYLOAD-ARGUMENT-COMPLETENESS-REPAIR-20260918-002`.

## Decision

**HOLD_NO_LEARNED_RESIDUAL_AFTER_ARGUMENT_COMPLETION**

Fresh harness-only successor to #1206. Only semantic collision normalization/audit changed. The representation, target_admissibility derivation, actual caller payload_ref augmentation, deterministic rule, #1133 seed/digest and decision gates were unchanged.

## First outcome

One primary invocation; reruns/replacements/post-result tuning0.

- exact #1133 rows regenerated:96/96;
- corpus semantic digest exact: `ea4a86baf3d2efc6f79f75703ef164d2c830cd3f5634e7ad057c26315da752dd`;
- exact acceptable-set membership: **96/96**;
- positive coverage: **48/48**;
- semantic-negative exact: **48/48**;
- false executable negatives: **0**;
- normalized incompatible structural signatures: **0**;
- missing required executable arguments: **0**;
- model/GUI/task-input actions:0.

Target IDs are alpha-renamed to current candidate slots and non-null payload values to `PAYLOAD_PRESENT` for collision analysis only. Exact proposal membership uses the original target and payload arguments. Construction explicitly showed different opaque IDs do not manufacture collisions while true CLICK-vs-YIELD / TYPE_TEXT-vs-YIELD differences do.

## Interpretation

On this purpose-built synthetic96-row corpus, once the already-retained #1177 target_admissibility field and one actual opaque payload_ref argument are caller-visible, the smallest frozen deterministic rule closes the entire corpus. There is therefore **no learned residual on this synthetic corpus**.

Do not train a classifier/MLP on these rows. The next high-information discriminator is a fresh retained/real-data collision census using this same typed contract. A real residual, if any, must come from real caller-visible states and independent acceptable-action evidence, not from synthetic omission or opaque-ID memorization.

This does not prove real desktop representation sufficiency or rule completeness in general.

## Integrity

Construction normalizer controls4/4. Source-first freeze/readback complete before primary. Mandatory ownership reread clean. Independent audit PASS/errors[]. Strict postformal copied-result verifier rejected5/5 mutations. Frozen source Git blobs remained unchanged after primary.

Raw primary:27,082 bytes, SHA-256 `82856d265ecfaff09558f27cb3f5c287202786d1d6341ab54f0b54314622aaf9`.
Audit SHA-256 `dffb23594477f754b708821b32c9af190482c5afe2c889f3d90637d4ba01c6a0`.
Corruption SHA-256 `c0dcd9f4dcbf0923d598d2ed3bbda52bde36cc83fd2fad831e8c662af83f3d7f`.

Full local raw primary bytes are not falsely claimed Git-retained; the exact rows are deterministic from the retained replay source/seed and the raw digest is recorded.
