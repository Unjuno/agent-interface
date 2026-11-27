# App Server timeout partial-usage regression

Date: 2026-11-03
Base: `cc99f9c8d1d7e99f10c297bbe3bece6e28fed288` (current main after PR #10163)

## Defect and repair

A timeout can occur after the App Server protocol journal has received a complete `thread/tokenUsage/updated` record but before `await_turn` returns a terminal turn. The adapter previously kept the journal slice but did not pass the known snapshot to the attempt ledger. In addition, Python's `asyncio.to_thread` path dropped custom attributes attached to a `TimeoutError`.

The adapter now harvests only complete newline-terminated usage records matching that exact thread and turn. It stores the latest usable fields as explicitly partial usage even when both primary token fields are present; malformed trailing JSONL is ignored. If exception-provided usage conflicts with the retained journal, it yields unavailable usage. The model-call bridge preserves the explicit partial status and returns exception metadata from the worker as data so it survives the thread boundary. The ledger still marks route totals incomplete for this timed-out attempt and leaves aggregate totals unknown.

## Regression evidence

- Unmodified current-main adapter + bridge with the new test: expected failure, exit 1. It recorded `usage=unavailable` despite 19 input tokens and 7 cached input tokens already present in the exact turn journal.
- Fixed composed App Server → provider-attempt recorder → public-MCP caller suite: 17/17 normal and 17/17 under `python -O`.
- The timeout case confirms no MCP tool call is submitted, records `status=timeout` with `status=partial`, retains raw response bytes, and keeps the ledger's aggregate `usage_status=incomplete` with unknown total input tokens.
- Logs and exit codes are retained here. Absolute local paths are redacted from the published log copies; byte-exact captures are retained in the task-local `LOCAL_ONLY/issue57_timeout_usage_partial_20261103_raw` directory.

## Scope

All tests use a fake App Server planner and a rejecting relay. This improves local accounting fidelity for interrupted attempts. It does not reconcile hidden provider retries or prove production provider accounting, live GUI behavior, WSLc/MAP01, efficiency, or broad reliability.
