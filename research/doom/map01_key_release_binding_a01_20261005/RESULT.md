# Key admission-to-release binding A02

Disposition: **PASS_METHOD_SCOPED** for the authored synthetic receipt contract.

The baseline bound `adm-1` to the same execution/step, one later confirmed `Down` up, and a later execution-scoped empty verification. The candidate rejected all six frozen mutations: duplicate admission ID, cross-execution up, up-before-admission, missing up, duplicate up, and unverified release. The separately implemented auditor agreed on all seven case names, decisions, and fault classes. Both scripts compiled in pinned WSLc.

Construction attempt A01 is retained as `HOLD_RUNNER_OUTPUT_MOUNT_MISCONFIGURED`; it evaluated no contract cases. A02 corrected this with an isolated writable `/out` mount and preserved the source read-only.

This result validates only a small authored measurement contract. It does not establish that runtime instrumentation emits these fields, that `up_confirmed` means physical key-up, that released input caused useful feedback, that recovery is bounded or effective, or that any live/task/MAP01 outcome improves. Continue the #59 prospective instrumentation and matched live threat gate under its own authority and allocation requirements.
