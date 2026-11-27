# Effect receipt handoff offline gate

- Scope: finite offline adapter integration on clean main base $head; source modifications are the candidate under evaluation.
- UTC evidence refresh: 2026-11-21T09:41:34.8720127Z
- Python: Python 3.11.9
- OS: Microsoft Windows NT 10.0.26300.0
- Temporary filesystem: $env:TEMP (C:\Users\user\AppData\Local\Temp), selected after recorder sync stalled on the configured D: temp volume.
- Normal exit: 0 (42 distinct tests)
- Optimized exit: 0 (42 distinct tests)
- Commands: python -u -m unittest research.integration.standard_mcp_task_ledger_57_v1.test_effect_receipt_handoff_v1 research.integration.standard_mcp_task_ledger_57_v1.test_recorded_comparison_adapter_v1 research.integration.standard_mcp_task_ledger_57_v1.test_comparison_measurement_v1 -v; python -O -u -m unittest research.integration.standard_mcp_task_ledger_57_v1.test_effect_receipt_handoff_v1 research.integration.standard_mcp_task_ledger_57_v1.test_recorded_comparison_adapter_v1 research.integration.standard_mcp_task_ledger_57_v1.test_comparison_measurement_v1 -v
- Coverage: same-action scorer/capture join; success baseline rejection; within-authority success; post-horizon factual-but-ineligible success; unknown and boundary-crossing timing; out-of-bracket effect; stale action; missing release horizon; matched-block validator composition; retained raw receipt digest; existing adapter and comparison-measurement suites.
- Scope limit: synthetic retained recorder evidence only. This is not live GUI/provider evidence and does not establish MAP01 success, caller reliability, integrated efficiency, distribution readiness, or research preview graduation.

- Candidate source commit: 001f9646b9416107de90fa26e1f6118d1839be71 (source files are unchanged by the evidence-format-only commit after this pin).
- Hash basis: SHA256SUMS.txt hashes packet bytes preserved by the local .gitattributes -text rule; source-sha256.txt hashes canonical Git blob bytes, obtainable with git show <commit>:<path>, to avoid Windows autocrlf ambiguity.

