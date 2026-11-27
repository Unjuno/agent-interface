# Current-main guarded stdio wait-budget recheck

Run date: 2026-10-18. Source revision: `fe678c1a0c94aac60a67d38e291fec69e3931e8c`.
This is a local recheck of existing tests, not a new formal/live allocation.
The frozen source list is in `SOURCE_FILES.json`; exact test-run output is in
`normal.txt` and `optimized.txt`.

Output SHA-256: normal `95af6f1c3b78604ce89aab29bc01874996862b4745ecac1ce646684b68f482db`,
optimized `6f5629b11f9b443536c6cd800b1a6a1cf530d1e37659f0d7eaa427761efc049d`;
source list `e7d20745c2b9bc2ee5143d84a0d177e2de5934ebae62452ccbea1e425856003a`.
Terminal padding whitespace was stripped from the retained text logs; test output content is unchanged.

## Result

All 19 tests passed in Python 3.13 normal mode (8.209 seconds) and optimized
mode (8.444 seconds). The suite combines the 14 cases in
`runtime.cli_v1.test_mcp_wait_budget` with the five cases in
`runtime.cli_v1.test_mcp_transport_cancellation`.

The real-stdio case pauses the Fake X server at release `sync`. The standard
MCP caller returns `pending` before the barrier resumes, reports neither
release-confirmed nor replay-allowed, keeps result lookup pending, and returns
`busy` for session close. After the harness resumes the server, the same call
finishes as `execution_failed` with verified Fake X cleanup. The in-process
cases also preserve busy admission across blocked press/release send, sync and
readback, with unknown task effect and no replay.

## Environment and limits

Python 3.13 had MCP/Pillow but not Xlib; Xlib was available in the existing
Python 3.11 site-packages. No packages were installed. To make the child
interpreter use the same local dependency path, the test harness passed the
parent environment through `StdioServerParameters`; the test source and
product code were unchanged. Run outputs preserve this recheck configuration.

The Fake X server resumes after a test barrier. These tests establish bounded
caller response and retained same-session custody for the named schedules; they
do not establish physical release, a native/server deadline, independent task
effect, MAP01 success, or matched efficiency. An actual backend/X server stop
can still leave physical release unknown.
