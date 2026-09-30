# Review correction for the v3 frozen audit

The v3 candidate/oracle corpus classifications remain byte-identical historical
evidence, but review found two fail-open holes in the v3 raw-only auditor: it
did not bind serialized case rows to the hash-pinned input corpus, and it did
not verify the selected `effect_id` against the qualified raw event. Therefore
the v3 audit PASS alone is insufficient to certify v3 result integrity.

Do not edit the v3 freeze, result, audit result, or v3 source. Successor v4
adds exact input-row binding and raw `effect_id` reconstruction, with two
post-classification corruption controls. The v4 disposition supersedes v3 only
for the stronger audit-integrity gate; it does not change the synthetic/live
scope boundary.
