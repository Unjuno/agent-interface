# Formal result — Needle cross-process package publication

Allocation: `needle-cross-process-publication-5045-v2-20260928-01` (Issue #5066), executed exactly once from the prospectively frozen branch. No retry or tuning.

## H/T/D/C/U

- **H:** independent reader processes should observe only a complete old/new role-skill package across a validated same-directory atomic publication; generation fencing should reject stale proposals. A deliberately unsafe in-place truncate/rewrite diagnostic arm should expose partial bytes.
- **T:** one publisher, four fresh reader processes per arm, 28 fixed queries across seven phases; local filesystem in one Linux/amd64 container. Exact seed-3788 package, candidate generation 3789. No model training, dispatch, or authority grant.
- **D:** validated atomic readers accept only generation 3788 before publication and 3789 after; invalid-candidate refusal preserves active bytes; stale generation yields; the unsafe diagnostic arm detects partial invalid bytes; frozen independent auditor and all corruption controls pass.
- **C:** the controlled contrast is publication method (atomic `os.replace` vs intentionally unsafe in-place rewrite), with package/input and finite schedule held fixed.
- **U:** synthetic single-host Linux local-filesystem publication/fencing only. This does not show real-time fine-tuning, LoRA quality/latency benefits, runtime integration, multi-host consistency, or power-loss durability.

## Result

**PASS_CROSS_PROCESS_PUBLICATION_SCOPED**. Runner exit 0; independent auditor exit 0; 28/28 observations retained; 12/12 corruption controls rejected; audit errors=[]; dispatches=0; authority_granted=false. In the atomic arm all 16 observations were complete and valid (old generation in the two prepublish phases, new generation in the postpublish and invalid-candidate phases). The diagnostic partial-write phase yielded four invalid/partial observations as designed; readers then saw the complete candidate after rewrite.

Raw JSON SHA-256: `9eff8dee4cdd98f2b3822ae11a6e203c35b09728598e743b03e55ca146897d3e`. Audit JSON SHA-256: `7ebafde1053b95ec60ac1071bf85d0adf985bd9da5a48b4e4620092086b082ca`. Execution record SHA-256: `faafd8b802f02b927916b5c7db44d5a0ea89ab64f3ec2528618aece4a2fe5dfe`. The full manifest and outputs are in this directory.

## Post-run diagnostic caveat (preserved, not a rerun)

The runner emitted a `runner_error.json` containing `SystemExit: 0` and an empty-message “error” even though its raw write and success stdout completed, process exit was 0, and the separate frozen auditor independently passed. Inspection traced this false-positive record to the frozen runner catching `BaseException` around the normal `raise SystemExit(main())`. This is an evidence-reporting defect, not a raw-data mutation or failed scientific gate; it is preserved verbatim in the bundle and is not silently deleted or relabeled. The current auditor does not reject this extraneous record. Future runner versions should catch `Exception` and add a regression that successful exit creates no runner_error file. The frozen allocation is consumed; no rerun will be made.

The data is available for integration/review; no broader product-performance claim is made.
