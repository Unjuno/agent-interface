#!/bin/sh
set -eu
evidence=/evidence/runs/optimized-timeout-1s
export PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/workspace DISPLAY=:88
export AGENT_INTERFACE_MCP_XVFB_TEST=1
export AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT="$evidence/result.json"
Xvfb :88 -screen 0 1024x768x24 -ac >"$evidence/xvfb-server.log" 2>&1 &
export AGENT_INTERFACE_XVFB_PID=$!
cleanup() { if kill -0 "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null; then kill -TERM "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null || true; fi; wait "$AGENT_INTERFACE_XVFB_PID" 2>/dev/null || true; }
trap cleanup EXIT HUP INT TERM
sleep 0.5
cd /workspace
if python3 -O -c 'import sys, unittest; import runtime.cli_v1.owned_guarded_session as owner; owner._XRES_DISCONNECT_TIMEOUT_S=1.0; name="runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb"; suite=unittest.defaultTestLoader.loadTestsFromName(name); result=unittest.TextTestRunner(verbosity=2).run(suite); sys.exit(0 if result.wasSuccessful() else 1)' >"$evidence/test.log" 2>&1; then rc=0; else rc=$?; fi
printf '%s\n' "$rc" >"$evidence/exit-code.txt"
cat "$evidence/test.log"
exit "$rc"
