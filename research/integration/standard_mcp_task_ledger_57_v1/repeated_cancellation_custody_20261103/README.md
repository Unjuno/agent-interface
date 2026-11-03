2026-11-03 repeated-cancellation custody regression

Hypothesis: the provider bridge loses custody if a caller cancels twice while the synchronous model worker is still running. The current-main baseline test reproduced this: the terminal ledger retained unavailable usage instead of the known 23 input / 5 output counts.

The bridge now repeatedly awaits the same worker task through `asyncio.shield`, so each caller cancellation is retained without cancelling the `to_thread` wrapper. Once the worker writes its terminal response, the bridge captures usage and exact raw bytes, and then re-raises cancellation. The public-MCP caller does not dispatch a tool call.

Validation: three relevant modules passed 32/32 in normal Python and 32/32 with `python -O`. The exact baseline failure, green logs, conditions, raw response, patch, exit codes, and SHA-256 manifest are retained here.

Scope: synthetic local provider/caller integration only. No live provider, hidden retry accounting, WSLc, MAP01, or reliability rate is established.
