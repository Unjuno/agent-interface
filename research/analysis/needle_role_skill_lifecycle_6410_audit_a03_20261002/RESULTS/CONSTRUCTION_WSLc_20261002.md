# WSLc construction-test record — Issue #6410 A03

**Disposition:** construction tests PASS (5/5); no scientific or audit result. The frozen raw-only auditor was not invoked.

- Allocation: `NEEDLE-ROLE-SKILL-LIFECYCLE-WSLC-6410-AUDIT-20261002-03`
- Frozen base: `926144e0bbbc197e00aa3b4821f1d49afe831529`
- Branch/package: `research/needle-role-skill-lifecycle-6410-audit-a03-20261002` / `research/analysis/needle_role_skill_lifecycle_6410_audit_a03_20261002/`
- Freeze SHA-256: `52d4fa62bceac0c8ba7a58b9288b66638fc47be9ea6c90c27ff99bfedea2f2fa`
- Test source SHA-256: `4aad2d445da496b74564a795e782b0df2ca85ebb661aeda4bfe6d3d19c79ad28`
- Runtime: Microsoft WSL Containers native CLI (`wslc.exe`) 3.0.1.0; cached `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`, image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`, Linux/amd64, CPython 3.12.14.
- Invocation: `wslc run --rm --pull never --network none --cpus 0.25 --memory 512m --user 65534:65534 -v <verified-stage>:/src:ro <pinned-image> python -B -m unittest discover -v -s /src/research/analysis/needle_role_skill_lifecycle_6410_audit_a03_20261002 -p test_*.py`
- Result: 5 tests passed in 3.753s; exit 0. Tests cover retained-fixture prediction reconstruction, explicit float32 round-trip, base-commit validation, and role A/B tensor reconstruction. WSLc warned that swap-limit capabilities/cgroup are unavailable; memory was limited without swap.
- The first attempted WSLc construction launch had an absent package path in the sparse-checkout bind mount and executed no tests. It was an environment/mount setup failure, not a candidate/auditor invocation. The package was then staged from the frozen Git tree, byte-normalized to the frozen checksums, checksum-verified, and the single successful test invocation above was run. Neither attempt executed the formal auditor.
- Pre-run `wslc ps` showed no running containers. No GPU, candidate, model, optimizer, training, timing, or raw reconstruction/audit was performed by this construction test.

## Gate and disposition

A03's frozen protocol requires an explicit bounded CPU/WSLc assignment and the current shared-runtime owner-release gate before the one-shot raw auditor. The latest inspected #5085 coordination record had no such A03 assignment. Accordingly auditor=0, candidate=0, retries=0. Do not treat an idle container snapshot or this construction PASS as authorization. Preserve allocation 02's `STOP_AUDIT_ENVIRONMENT_PATH` unchanged. No hypothesis PASS/FAIL/HOLD is claimed.

This record is additive and does not alter the immutable raw, prior STOPs, or frozen source.