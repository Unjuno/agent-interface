2026-11-03 local Fake provider cancellation custody experiment

The synchronous model worker cannot be stopped by asyncio task cancellation. The adapter therefore keeps custody until the worker exits, captures terminal usage and raw response bytes, and then re-raises `CancelledError`. The recorder validates and durably stores those exception-carried fields before propagating cancellation. The composed public-MCP layer sends no tool call.

The new composed regression failed before the fix because `CancelledError` was swallowed and returned as an ordinary result. After the fix, the cancellation composition regression, existing integrated timeout regression, and existing recorder cancellation regression passed in normal Python and `python -O`; full logs and exit codes are retained. `synthetic-provider-events.jsonl` is the exact response payload used by the test.

Scope: local synthetic adapter evidence only. It does not establish live-provider behavior, hidden retry accounting, WSLc/MAP01 qualification, or reliability rates.
