# T8 formal outcome — PASS_RETAINED_RECEIPT_SCHEMA_AUDIT

The single offline CLI validation accepted the exact retained T7 auditor stdout. Its SHA-256 remained `604fc18e94e80f6aa941623b8854ffad88043e16e5058db89aa45449ba97489f` (306 bytes) before and after validation. The frozen receipt values matched: 432 rows, 432 unique cases, 432 independent row matches, semantic SHA-256 `a7bd0adc9485df7161b7ce85c27b1dc58fad71ee2fee9cfe081cc61337b0e193`, task-fallback wrong-target count 27, yield-fallback wrong-target count 0, zero authority grants, and no errors.

The corrected verifier checks the auditor's actual field name `failed_probe_yield_wrong_target`. The prior T7 verifier's expected alias remains frozen and unchanged; T7 therefore remains **STOP_HOST_RECEIPT_SCHEMA_MISMATCH**. This PASS supplements T7 by independently confirming that the captured auditor receipt itself has the preregistered values. It does not retroactively satisfy T7's frozen host-verifier gate.

Eight mutation tests passed before the formal CLI check. The formal CLI ran once with Python 3.12.10 and the standard library only, exited 0 in 130 ms, and emitted `PASS_RETAINED_RECEIPT_SCHEMA_AUDIT`. Candidate, WSLc, and Docker invocations: 0; retries: 0.

No Docker/native comparison, performance or memory/OOM claim, GUI/model/application effect, or change to #5309/T6 history follows from this offline receipt audit.
