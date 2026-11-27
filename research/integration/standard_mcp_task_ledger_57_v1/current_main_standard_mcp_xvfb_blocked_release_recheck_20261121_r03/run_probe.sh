#!/bin/sh
set -eu
attempt=${1:?optimized-01|optimized-02|optimized-03}
case "$attempt" in optimized-01|optimized-02|optimized-03) ;; *) exit 2 ;; esac
evidence=/evidence/runs/$attempt
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace DISPLAY=:88
export AGENT_INTERFACE_MCP_XVFB_TEST=1
export AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT="$evidence/result.json"
Xvfb :88 -screen 0 1024x768x24 -ac >"$evidence/xvfb-server.log" 2>&1 &
export AGENT_INTERFACE_XVFB_PID=$!
cleanup() { if kill -0 "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null; then kill -TERM "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null || true; fi; wait "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null || true; }
trap cleanup EXIT HUP INT TERM
sleep 0.5
cd /workspace
test_name=runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb
if python3 -O -m unittest -v "$test_name" >"$evidence/test.log" 2>&1; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" >"$evidence/exit-code.txt"
cat "$evidence/test.log"
exit "$rc"
