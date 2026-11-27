# Win32 GUI queue-stall timing attempt r05

Date: 2026-11-10 (Asia/Tokyo). Source route: `supervised-win32`, main `002947dcc55a9f7ebd56fcccc35af328cfabca04`.

## Outcome

The target fixture's message pump was configured to block for 8 s, but probe setup took about 55 s from fixture readiness to dispatch. The pump had resumed roughly 47 s before dispatch. The single A action completed and release/horizon receipts were returned, but the fixture `WM_CHAR` occurred 62 ms before horizon start. This run did not test queued input during a blocked message pump or any post-horizon application effect.

Classification: `METHOD_FAIL_TIMING_WINDOW`. The window was closed and the exact fixture process exited. Preserve this run as a harness timing failure; do not count it as a positive or negative safety result.

Raw conditions, source, public MCP requests/results, process logs, event timestamps, terminal custody, cleanup and a SHA-256 manifest are retained here.
