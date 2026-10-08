# MCP result status survives host presentation

The actual primary host adapter forwarded content but dropped the explicit MCP isError flag. New regression tests reproduced two failures: identical content lost true/false distinction, and an empty-content error displayed nothing. The presenter now emits an explicit status text object before unchanged content when the flag exists; it never infers an absent flag.

Validation: 22 Node tests passed, including current-error preservation while an identical image is referenced to an earlier reviewed base. Full native protocol/harness checks passed. The primary agent used the changed presenter on retained successful-inspection and failed-review responses from inspection-error-flag-primary-01 and received false/true respectively, alongside the original Calc image/body. This was a read-only presentation check; no task input, capture, retry or allocation was executed. Historical records are unchanged.

The status describes tool execution, not task correctness. No latency, token savings or new GUI reliability claim. The small extra text is intentional outcome information.

raw.tar.gz retains exact before/after logs, native-check logs/result, the two original replies, displayed-status summary and changed source/tests. manifest.json pins every member. The input program/runtime archive is unchanged.
