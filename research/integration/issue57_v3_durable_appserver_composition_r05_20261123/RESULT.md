# Issue #57 successful effect with UNKNOWN usage R05 - 2026-11-23

## Result

**PASS_SYNTHETIC_SUCCESS_WITH_UNKNOWN_USAGE_HELD_FROM_COMPARISON.** On
current main 8a9cb6d9b99b724732f3baf3caee83d2f043c0bb, a synthetic valid
JSONL App Server answer completed without a tokenUsage notification. The real
provider adapter/caller path preserved the completed attempt, exact call/thread
IDs, and synthetic independent task effect as TASK_SUCCEEDED. All five usage
totals remained None. The durable task custodian audited both execution and
effect receipts, while the frozen comparison projector returned HOLD with
usage_incomplete_or_invalid; the run stayed HOLD with 17 assignments missing
and dispatch disabled.

The focused test passed 1/1 and the full nine-test transport/custody module
passed 9/9 in normal and optimized modes on Windows CPython 3.13.14 with Pillow
12.2.0. Raw output and exit codes are preserved.

## Limits

The App Server peer, task execution and effect score are synthetic, and the
allocation verifier is injected. No live provider, GUI, native input, external
allocation, Docker or WSLc was used. This verifies only the fail-closed
comparison boundary: it does not establish live provider completeness or
efficiency. The caller's task effect remains recorded as successful; only the
comparison row is ineligible. Keep Issue #57 open.

See CONDITIONS.json, result.json, raw .bin outputs and SHA256SUMS.
