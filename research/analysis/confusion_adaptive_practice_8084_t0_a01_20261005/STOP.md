# A01 — `STOP_PREFORMAL_INPUT_ISOLATION`

No formal candidate or auditor invocation occurred. During pre-run mount review, the planned package-wide candidate mount would have made the scorer/held-out fixture accessible to the candidate process, despite the candidate's current code not needing those fields. That fails the frozen no-held-out-leak boundary. Construction tests were not a formal result. Preserve this freeze and its source/tests unchanged; do not retry A01. A02 is a fresh allocation with an explicit candidate allowlist mount and a separate auditor-only scorer fixture.

