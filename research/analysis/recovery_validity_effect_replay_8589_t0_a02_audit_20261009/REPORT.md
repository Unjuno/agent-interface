# Result: independent audit of Issue #8589 A01's left-only decision gate

**Result: `PASS_AUDIT_ONLY_LEFT_GATE`.** One new independent auditor invocation reconstructed the required complete left-only case from A01's frozen input and retained raw. The selective policy recomputes only `derive_left` (1 node), while the preregistered earliest-conflict suffix recomputes `derive_left`, `derive_right`, and `prepare_right` (3 nodes). The exact raw lists match an independent read-set/dependency reconstruction, and the case has complete provenance with only integer `left_cfg` advancing from 1 to 2. No effect dispatch appears.

The `boolean_version_alias` case has a Boolean where an integer generation is required. The new auditor confirms it is not a valid generation-typed case and does not use it as the decision discriminator. Thus the earlier correction's specific statement that the retained raw did not demonstrate the required left-only advantage is contradicted by this audit.

This allocation is audit-only. It did not run the A01 candidate, rerun A01's auditor, modify A01 files, or test any GUI, model, runtime, or real effect. It confirms only the narrow left-only gate condition; it does not independently reconstruct all A01 cases or revise A01's overall formal classification. The original A01 auditor's overly broad advantage aggregation remains a defect in the original audit implementation, even though the required left-only condition is independently shown to hold.

## Reproduction and evidence

- Current-main base: `4758a95cd4a0aaa78e9cdc9d774f298d4ccf0e36`.
- Allocation: `8589-A01-LEFT-GATE-AUDIT-ONLY-20261009`.
- Frozen source copies, hashes, protocol, and auditor: `FREEZE.json`, `source/`, `PROTOCOL.md`, `auditor.py`.
- Formal command: `python3 research/analysis/recovery_validity_effect_replay_8589_t0_a02_audit_20261009/auditor.py research/analysis/recovery_validity_effect_replay_8589_t0_a02_audit_20261009/results/audit.json`.
- Formal invocations: candidate 0; A01 auditor 0; new auditor 1; retries 0. Exit code 0.
- Complete machine-readable result: `results/audit.json`.
