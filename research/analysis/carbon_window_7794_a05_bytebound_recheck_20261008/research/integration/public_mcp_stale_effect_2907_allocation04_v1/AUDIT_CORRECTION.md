# Versioned read-only audit correction for allocation 04

This is an additive audit correction under the same #2907 question; it does not modify, replace, or upgrade the first audit or formal bundle.

## Preserved first audit

The allocation-04 formal run remains `PASS_PUBLIC_MCP_STALE_EFFECT_RELEASE_SCOPED`. Raw SHA-256s: result `38125998c85525e925108fb66b6218953339d710b4d04c40ca494b282c773906`; trace `08bbfcbb8d474701cabbcf13a1b83b771fb03053185e38a34ec4a828fdb3bcf8`; persisted title effect receipt `cec3a93cd1694c494df334c90b0f303c5d50a962fe1985689a985254e24dae9a`.

The first independent Docker audit is retained as `HOLD_RAW_AUDIT`, errors=[], with one of its six reported corruption controls (`split-retained-transport`) not rejected. Its exact audit JSON SHA-256 is `9caf0766acdaf4259edd8e7858c5e948b21baa9ee38c821d43f0cc407617ab5e`. It also omitted the separately specified persisted-effect mutation control. Do not edit or overwrite this result.

## Correction and pre-audit verification

The bug was in auditor control composition: transport validation was only reached when the parent auditor had already emitted a retained-read error; on this valid bundle, mutating `same_client_context=false` therefore returned no error. The first auditor also started its control set at the base audit, omitting the persisted-effect mutation control.

New read-only auditor: `auditor_effect_v4.py`, SHA-256 `22b329936677aa8a239f15abb98557c21c3aff219db79daaa57b19e50bfe6de1`. Construction test `test_auditor_v4.py`, SHA-256 `5e6a98ec6feb6bd1e310a85e5e4ba24716a840ea9809b10100310e175c6583d4`. Both files are committed to this branch and were byte-exact readback verified. Its local Docker construction test passed and proves transport-split and call-ID mismatch are rejected even when the unmutated read bundle is otherwise valid.

The corrected auditor independently checks the raw response bytes, effect receipt, all six retained-result call IDs/states/no-op flags, a single ClientSession transport binding, and eight corruption controls: the five base controls plus persisted-effect mutation, transport split and retained call-ID mismatch. It makes no MCP call or input.

## One corrected read-only audit

Run the exact same allocation-04 `formal04/` bytes once; write to a new output `audit04-corrected/`. Use a separate local Docker container with `--network none --read-only`. Mount the formal bundle and all auditor dependencies read-only; only the new audit output is writable. The exact-source identities and original HOLD remain immutable. This is a versioned offline re-audit under #2789's same-question auditor-correction path, not another formal experiment or a claim of runtime integration completion.
