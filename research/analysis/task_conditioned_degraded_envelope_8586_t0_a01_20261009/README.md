# Task-conditioned degraded configuration envelope — Issue #8586 T0 A01

This package tests the finite method proposal in [Issue #8586](https://github.com/Unjuno/agent-interface/issues/8586). It compares task-conditioned route eligibility with independent fallback-edge composition and blanket stop under every loss subset of six capabilities across three task classes and six contexts.

The frozen grid contains 1,152 rows. Its planned discriminator is the `preserve_sibling_edit` task with simultaneous loss of `semantic_target` and `native_effect_check`: the naive edge baseline combines pixel targeting and visual-difference verification even though that route cannot prove `sibling_unchanged`. The same model includes supported single-loss routes, so blanket stop is also tested for false refusal.

## T0 A01 result

**`PASS_METHOD_SCOPED`** for the frozen finite model. Candidate and independent raw-only auditor each ran once; retries were zero. The auditor reconstructed all 1,152 rows with zero errors and zero TDCE/oracle mismatches. It counted 114 feasible TDCE rows; the edge-wise fallback baseline made two false continuations when both `semantic_target` and `native_effect_check` were lost (one row also lost the unrelated `read_action` capability), while blanket stop refused 107 feasible rows. TDCE made zero false continuations and zero false stops in the enumerated model.

The 10 construction/mutation tests passed in normal and optimized Python before the freeze. They reject missing rows, a forged route proof, hidden task obligations or hard gates, a forged compensator, an expired allowance, a permissive UNKNOWN, and the joint-loss false continuation. The frozen candidate raw is 1,194,522 bytes; source identities, run receipts, results and hashes are in [FREEZE.json](FREEZE.json), [RUN_RECORD.json](RUN_RECORD.json), and [SHA256SUMS.txt](SHA256SUMS.txt).

This is an authored finite-model result only. It does not establish that these capability losses occur in production or that an envelope improves runtime safety, reliability, latency, or product behavior. No live GUI, model, OS input, user data, external effect, or container was used; runtime code and authority were unchanged.

Scope is limited to this authored finite model. No live GUI, model, runtime, user data, external effect, safety, or product behavior is tested. No production capability-loss frequency or runtime integration is claimed.
