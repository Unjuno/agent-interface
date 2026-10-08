# #7949 A03 — repeated disjoint-write replay

## H / T / D / C / U

**H.** A02 is a STOP because its runner exit status was not captured; it supplies no scientific evidence. A03 independently tests whether explicit complete event replay preserves the latest value after two sequential writes to an unrelated field while recovering the agent-owned field. It also exercises the A02 finite boundary cases in a separately frozen allocation.

**T.** Deterministic standard-library simulator; no GUI, model, user data, OS input, network, or runtime mutation. Ten frozen prior-shaped cases plus `two_disjoint_writes`, where an external writer sets `y=9` then `y=11` under consecutive sequence/global/field revisions. Candidate sees event journal and final snapshot only, not a supplied conflict flag. Candidate and raw-only independent auditor each run exactly once after freeze.

**D.** PASS only if all 11 rows reconcile as frozen, `two_disjoint_writes` field compensation yields `{x:0,y:11}`, its blind inverse loses the external `y`, whole-object guard refuses changed global revision, unsafe same-field/ABA/replacement cases do not compensate, integrity anomalies are UNKNOWN, compensation is a distinct semantic effect and makes no exact-rollback claim, corruption mutations are rejected, and audit errors are zero. Otherwise FAIL/HOLD; any orchestration or preflight uncertainty is STOP. No retry.

**C.** Authored finite histories and revisions only. This does not show a real application provides complete journals, atomic compare-and-compensate, stable identities, or valid coverage certificates.

**U.** No native GUI, live external actor, application semantics, authority, user effect, or production safety is tested. No runtime integration follows from a PASS.

## Provenance and execution

Issue #7949; prior A01/PR #7971 is historical and untouched. A02 is separately preserved as `STOP_WRAPPER_EXIT_UNCAPTURED`; its stdout is not interpreted. Intake main: `9fb2dd6782d1d1477a00d14be870487fd4c54fa2`. This A03 uses the same isolated research branch but a distinct additive path and run ID. Native macOS CPython stdlib is used; OrbStack's read-only image inventory failed with containerd `operation not supported`, and no VM/container state will be changed. Freeze all source/input hashes before the one candidate and one auditor invocation. Capture process status from the execution API result; do not assign zsh's reserved `status` variable. Preserve outputs and issue evidence. No retry or replacement within this allocation.
