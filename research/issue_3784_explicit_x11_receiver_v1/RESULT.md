# Issue #3784 formal-01 result

## Disposition: STOP — harness control-oracle defect

The frozen four-row allocation ran once in the pinned no-network Docker image. All four fresh Xvfb servers were reaped. In each row, the mapped InputOnly receiver held focus and recorded the receiver-only XTEST `a` KeyPress and KeyRelease; both events decoded as `a` through XLookupString.

The runner nevertheless stopped before baseline/map capture and before importing or invoking the candidate backend. Its control predicate expected XLookupString to return an empty string for KeyRelease. The frozen construction gate and the formal observations show that expectation is false in this environment. Therefore `receiver_control_ok` was false in all four rows, but the observed receiver mechanism itself did receive the control. No candidate formula events, German layout changes, or semantic candidate outcome were tested. The original H remains unresolved.

This is not a candidate FAIL and not evidence for/against German formula delivery. No retry or post-outcome edit was made to the frozen runner or raw.

## Audit record

- Raw disposition: `STOP_GERMAN_FORMULA_DELIVERY`
- Raw SHA-256: `34f6e18f90a0af9af75c3fdecf74297f9b562e052b139b076b1aaa060edf9859`
- Frozen audit-v1 SHA-256: `5128bf19b19e5bf09e7210c9e31aaed827fabf331dd095a67eec65b9e94ff01d` (`audits/formal-01/audit-frozen-v1.json`)
- Frozen audit-v1 disposition: `FAIL_AUDIT_INTEGRITY`; it also classified the missing map captures as integrity errors, although those later-stage artifacts were not reached after the registered early STOP.
- Separate read-only forensic audit-v2 SHA-256: `f70a7eb413cb1f897485d8a7becf19c456865c72d1ca684446fa8ef28d29e07e` (`audits/formal-01/audit-stop-v2.json`)
- Audit-v2 disposition: `PASS_AUDIT_CONFIRMED_HARNESS_STOP`, zero errors. It binds the raw/source hashes, all four control traces, focus identity, absence of candidate-plan/events, and Xvfb reaping. It is an explicitly post-result forensic addendum; it does not replace or mutate the preregistered audit-v1.

The separate audit outputs are both retained so the auditor limitation is visible. Construction evidence is only a mechanism check (1/1) and is not formal result evidence.

## Scope and next gate

This allocation establishes only that the private InputOnly receiver received the control events under the pinned image. It does not test the German map or candidate formula. A successor must use a new allocation ID and path, preserve this raw/audit pair unchanged, correct the release-event oracle, independently test that oracle in construction, then proceed to the four-row candidate gate only if the receiver control is sound. Do not claim that `-noreset` caused map persistence.
