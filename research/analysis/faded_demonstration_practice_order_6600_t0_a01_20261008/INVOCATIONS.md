# Formal invocation ledger

Allocation: `FADED-PRACTICE-ORDER-6600-T0-A01-20261008`

Preregistration was posted to Issue #6600 before these commands: https://github.com/Unjuno/agent-interface/issues/6600#issuecomment-6051375777

1. Candidate invoked once after preregistration. Exit 0. Stdout: `{"status": "CANDIDATE_COMPLETE", "arms": 2, "rows": 12}`. Output: `RAW.json`, SHA-256 `f56ed0efef12fddc3b3ee8cc257847d31a7bce90cc8882220a428a9995988bca`.
2. Independent auditor invoked once, conditional on candidate exit 0. Exit 0. Stdout: `{"status": "PASS_METHOD_SCOPED", "errors": [], "rows_per_arm": 6, "mutations_rejected": 6}`. Output: `AUDIT.json`, SHA-256 `e62e0b60f2cddcaa650860bc43779539c17c71c513a3db6a4a8e7936d0157076`.

Retries and reruns: 0. No other formal candidate or auditor invocations occurred. Construction tests are not counted as formal invocations. Host-only stdlib environment; no container or effectful action.
