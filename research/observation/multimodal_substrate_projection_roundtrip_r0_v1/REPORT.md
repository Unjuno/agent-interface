# #1602 retained formal integrity stop

Runner decision: **FAIL_SUBSTRATE_SEMANTICS**.
Scientific disposition: **NONE — consumed integrity/accounting stop; no rerun**.

The first and only frozen formal invocation completed 120,000 traces and produced zero candidate/oracle mismatches, zero direct projection mutations, zero modality-conflict overwrites, zero old-version mutations, zero compaction semantic changes, 20,000 cross-entity refusals, 20,000 expiry refusals, 120,000 forged-projection refusals and 40,000 valid revalidations. The unsafe SUMMARY_REHYDRATE discriminator produced 120,000 false-current outcomes and 179,986 laundered fields.

However two post-result contradictions invalidate the runner's scientific decision:

1. The `omitted_field_syntheses` metric increments when a proposal value merely equals an already-existing canonical value. It does not require before/after canonical mutation. Fourteen random omission rows therefore count as syntheses even though the independently measured direct projection mutation count is exactly zero and candidate/oracle full-state comparison is zero.
2. The independent audit expected exactly 20,000 stale-projection rejections, while the frozen formal intentionally increments that same counter for both the 20,000 `stale` rows and 20,000 `aba` rows. The preregistered gate required >=20,000, so the audit's exact-20,000 condition is inconsistent with the source.

These are measurement/accounting defects, not evidence of a projection-origin canonical write. The frozen result must not be relabeled PASS and must not be rerun. A fresh successor may change only (a) omission synthesis accounting to require an actual before/after canonical change attributable to an omitted returned field and (b) audit accounting to separate stale-version and ABA rejection counters. Science, corpus, seed schedule, candidate/oracle semantics and unsafe baseline remain fixed.

Formal invocation1; reruns0; replacements0; tuning0.

Evidence hashes:
- FORMAL_RESULT.json SHA-256 `140895ced8c029bb0584b01cf10916e252d029b232c0feef683490cbcde0fdaf`
- AUDIT.json SHA-256 `74f79f676755d5cc311e8a00b7cd5690ef69a4033f4c2d972a9db67643d5c117`
- frozen source bundle Git blob `fcf161ae396fe267d70536b24802a6ab885df3a3`
- frozen source bundle text SHA-256 `af2567a69eafc7114ed92ebc7c392593086adb5cef20e72403fbd18f4b82d52a`

Scope remains synthetic standard-library semantics only; no model/GUI/runtime promotion claim.
