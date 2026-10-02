# Posthoc adjudication — Issue #6689 allocation 01

**Final decision: `FAIL_METHOD`.** This is an additive qualification of the retained raw/audit; it is not a rerun or replacement audit.

The preregistered acceptance rule requires a decisive negative to preserve outstanding obligations. The frozen state has a `mandatory_fail` event and a separate `mandatory_all_pass` marker; if `mandatory_fail` is true while `mandatory_all_pass` is false, no event says that the remaining mandatory-check vector completed. Nevertheless, candidate and auditor both add `mandatory_check_vector` to `pending_obligations` only when *both* `mandatory_fail` and `mandatory_all_pass` are false. Thus a decisive negative silently drops the unresolved vector.

Read-only analysis of the retained candidate raw found 192 states classified `STABLE_FINAL_FAIL` with `mandatory_fail=true` and no `mandatory_check_vector` pending. A concrete shortest representative prefix is `mandatory_fail`, `generation_sealed`; its sources remain open, `mandatory_all_pass=false`, and the pending list contains only source completion. The auditor duplicated the same completion assumption, so its four rejected mutations do not rescue the acceptance gate.

Preserve the original emitted auditor status `PASS_METHOD_SCOPED`, raw SHA-256 `f95ef664ebfc663a784747297e493dc3c5cd0e4b1adc8d26e9c2bb7e887644e3`, and audit JSON SHA-256 `e093260fe645a5ebb2476a18f3b366f1f98200cf3e4586d3a992fd6c6e999b2a`. Candidate/auditor/retries are 1/1/0; this allocation is consumed. No repaired source, retry, or substitute result is offered here. Any future testing must be a separately frozen successor with an explicit mandatory-vector completion event and independent control that checks obligation preservation.
