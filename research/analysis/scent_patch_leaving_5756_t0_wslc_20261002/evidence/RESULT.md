# Result — SCENT-PATCH-LEAVING-5756-20261002-01

## Disposition

**STOP_AUDIT_SCHEMA — no scientific verdict.** The candidate completed once under WSLc and the independent auditor completed once, both exit 0. The auditor emitted `FAIL_METHOD`, but its unsafe-edge predicate is not semantically valid for the candidate's evidence field: `unsafe_transition` is set when an unsafe edge is *encountered and excluded*, while the auditor treats any true value as an unsafe traversal. The raw record does not distinguish attempted/excluded from traversed. Therefore the method gate is not interpretable, and the frozen zero-retry rule applies. Do not alter or rerun this allocation; any corrected schema requires a distinct successor allocation.

## Retained evidence

- WSLc 3.0.1.0; kernel 6.18.40.1-1; linux/amd64 Python image digest `python@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f`; image ID `sha256:9e87977b867847e186d066f531ef783b006d582a985c341c269446088d90f2c4`; Python 3.12.14.
- Candidate: 120 graphs × 3 policies = 360 rows, exit 0, raw SHA-256 `a6ec1d39254aa0f8a5070f9aeae7da87aa1d2a909d36cb4363ea1bb8fe0f7acc`.
- Independent auditor: exit 0, four mutation controls rejected, `FAIL_METHOD` solely including `unsafe edge traversed`; see `auditor_stdout.txt`.
- Held-out descriptive rows (not an interpretable result): each policy 36/60 successes; mean cost among successes was 117.17 fixed-depth, 109.67 exhaust-branch, 105.67 patch-leave. Since the method gate failed, these values do not support H and are not a valid policy comparison.
- WSLc warned: “Your kernel does not support swap limit capabilities or the cgroup is not mounted. Memory limited without swap.” The candidate and audit containers exited normally. Post-run inventory is recorded in `containers_after.txt`.
- The earlier unrelated `python --version` WSLc smoke container also appears in the inventory; it was read-only/no-network and ended before this allocation. No container was stopped or removed.

## Scope

This is a synthetic CPU method attempt only. No GUI/model/GPU/network/live effect. The result does not alter #5756's prior T0 (`PASS_METHOD_SCOPED` in PR #5779) or establish/deny live benefit. Preserve all evidence unchanged.
