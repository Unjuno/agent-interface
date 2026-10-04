# Key admission-to-release binding A03

Disposition: **PASS_METHOD_SCOPED** for the authored synthetic receipt contract, after retaining two earlier construction failures.

The baseline bound `adm-1` to the same execution/step, one later confirmed `Down` up, and a later execution-scoped empty verification. In A03, the candidate rejected all six frozen mutations—duplicate admission ID, cross-execution up, up-before-admission, missing up, duplicate up, and unverified release—with the exact preregistered reason. Candidate, independent auditor, and compile commands each returned exit code 0 in pinned WSLc. The auditor agreed on all seven case names, decisions, and reason labels.

Construction attempt A01 is retained as `HOLD_RUNNER_OUTPUT_MOUNT_MISCONFIGURED`; it evaluated no contract cases. A02's candidate output is preserved but its frozen expected-reason labels disagreed with the semantic rejection reasons on four cases; the independent oracle's PASS does not erase that `FAIL_METHOD`. A03 froze the corrected labels and audited declarations against the oracle before running.

This result validates only a small authored measurement contract. It does not establish that runtime instrumentation emits these fields, that `up_confirmed` means physical key-up, that released input caused useful feedback, that recovery is bounded or effective, or that any live/task/MAP01 outcome improves. Continue the #59 prospective instrumentation and matched live threat gate under its own authority and allocation requirements.
