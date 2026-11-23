# Current-main public recovery writer-drain R05

Frozen source: d5a378ecfd0d6fd71804fc509f9d6ecd31be0dd1
Question: Does current-main test revision 1bf4d236 (which added exact report-temp draining and server-close waiting after R04) eliminate the old R04's observation-timeout/temporary-report cleanup symptom in its exact fake lifecycle test?

Test: runtime.cli_v1.test_mcp_supervised_win32.SupervisedWin32MCPTests.test_public_compiled_caller_joins_exact_result_query_and_task_oracle
Cohort: exactly one fresh Python process in normal mode and one fresh process under -O, in this fixed order. No retries/replacements.
Acceptance per mode: the exact unittest exits 0, reports 1/1 OK, retains action UNKNOWN and replay denied, separately verifies recovery/release/horizon and exact fixture task oracle, and leaves no `.report.json.tmp` at teardown. Any failure remains failed; no timing/deadline relaxation.
Scope: local Fake Win32 producer/owner, fake observation callback, synthetic effect/oracle. No native input, real GUI, provider, Docker, WSLc, or formal allocation.
Runtime: Windows CPython 3.11.9. Full stdout/stderr, exit code, UTC start/finish, source hash, and audit are retained.
Frozen test source SHA-256: 40d29866b0f09e3491d99ec5a71014a5103c16c4ae07f743ce4b95e3fa31e358
