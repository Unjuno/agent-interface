# Win32 GUI queue-stall timing attempt r06

Date: 2026-11-10 (Asia/Tokyo). Source route: `supervised-win32`, main `002947dcc55a9f7ebd56fcccc35af328cfabca04`.

## Outcome

This attempt shortened setup and configured a 10 s message-pump block. Public observation did not finish until about 9.2 s after fixture readiness, so the pump resumed before dispatch began. The A event arrived 63 ms before the completion horizon started. The action completed and release/horizon receipts were valid, but the intended blocked-queue timing was not achieved.

Classification: `METHOD_FAIL_WINDOW_ALREADY_RESPONSIVE_AT_DISPATCH`. The fixture was closed and exited. This run does not establish queued input while blocked or a post-horizon effect; keep it separate from r07.

Raw conditions, source, public MCP requests/results, process logs, event timestamps, terminal custody, cleanup and a SHA-256 manifest are retained here.
