# Cross-process role-skill reload — formal result

Issue #3890; predecessor #3780; allocation `needle-role-skill-cross-process-reload-v1`.

## Decision

`PASS_ROLE_SKILL_CROSS_PROCESS_SCOPED` on the preregistered 3-seed synthetic allocation. Independent audit: `PASS_AUDIT_SCOPED`, zero errors. All three builder runs and six clean loader runs completed in local Docker with network disabled, CPU limit 1, 2 GiB memory limit, and the cached `needle-pilot05:local` image (`sha256:6ab7a93188dd60d3832a0be8b5266418e0de1253159c5c66e64562a85fd4a10e`). Builder source was read-only; every loader used the package read-only and wrote only to its own output mount. No formal run was retried.

| Seed | Role A | Role B | Role C | Both fresh loaders exact on 12,288 rows |
|---:|---:|---:|---:|:---:|
| 3788 | 0.967529 | 0.903076 | 0.928223 | yes |
| 3789 | 0.970215 | 0.905273 | 0.900635 | yes |
| 3790 | 0.961914 | 0.923584 | 0.947021 | yes |

All role accuracies meet the preregistered >=0.90 threshold. Seed 3789 / role C is a narrow pass (0.000635 above threshold); this should motivate a separately preregistered robustness follow-up, not post-hoc seed replacement. Each fresh loader reconstructed model calculations from the JSON tensor artifact and reproduced all builder-heldout predictions exactly. In both fresh graph generations it rejected stale-generation receipts and completed A→B→C. Tampered digest, truncated JSON, unknown schema, wrong adapter version, skipped edge, wrong scope, duplicate receipt, unverified outcome, and unknown destination controls yielded as specified; rejected transitions did not change graph state or fixture emission count.

## Evidence and provenance

The builder outputs and two loader outputs per seed are retained under `formal/seed-3788/`, `formal/seed-3789/`, and `formal/seed-3790/`. `formal/audit.json` is the retained independent audit output. `formal/FREEZE.json` preserves the allocation copy; the authoritative frozen source, image ID, and retired construction seeds are recorded in `FREEZE.json`. Construction-only seeds 3781–3783, 3787, and 3791 are excluded and documented in `audit/CONSTRUCTION_ONLY_STOP.md`.

The post-formal auditor initially stopped because its path/manifest reader expected a different evidence layout and the freeze record had a one-character loader-hash transcription error. Raw formal outputs were not changed or rerun. These independent-audit corrections and the exact recomputation on the same retained raw evidence are documented in `AUDIT_SOURCE_CORRECTION.md`; the resulting audit is zero-error. This scoped PASS depends on that corrected auditor, not the initial STOP.

## Scope limits

This establishes a bounded synthetic JSON serialize/reload lifecycle, not production skill transfer, artifact authenticity (SHA-256 is not a signature), hostile-input security, concurrent updates, real actuator effects, or execution authority. The graph and receipts are fixture-only. The retained inputs include synthetic held-out vectors to permit independent reproduction; they are not real user data.
