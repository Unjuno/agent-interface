#!/usr/bin/env bash
set -u
ROOT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/work/goal-currentmain-recovery-20261022
RAW="$ROOT/research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-01/raw"
if test -S /tmp/.X11-unix/X88; then echo DISPLAY_88_BECAME_BUSY >&2; exit 70; fi
/usr/bin/Xvfb :88 -nolisten tcp -screen 0 1024x768x24 -ac > "$RAW/xvfb.log" 2>&1 < /dev/null &
PID=$!
printf '%s\n' "$PID" > "$RAW/xvfb.pid"
ready=0
for i in $(seq 1 50); do
  if test -S /tmp/.X11-unix/X88 && kill -0 "$PID" 2>/dev/null; then ready=1; break; fi
  sleep 0.1
done
if test "$ready" != 1; then
  echo XVFB_READINESS_FAILED >&2
  kill -INT "$PID" 2>/dev/null || true
  exit 71
fi
readlink "/proc/$PID/exe" > "$RAW/xvfb-executable.txt"
cd "$ROOT" || exit 72
set +e
DISPLAY=:88 PYTHONPATH=/tmp/agent-interface-codex-deps-20261022-r01 \
AGENT_INTERFACE_MCP_XVFB_TEST=1 \
AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=1 \
AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS=1 \
AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=1.0 \
AGENT_INTERFACE_XVFB_PID="$PID" \
AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT=research/integration/standard_caller_xvfb_current_main_20261022/prestarted-fresh-recovery-01/raw/result.json \
python3 -m unittest -v runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb \
  > "$RAW/stdout.txt" 2> "$RAW/stderr.txt"
RC=$?
printf '%s\n' "$RC" > "$RAW/exit-code.txt"
kill -INT "$PID" 2>/dev/null || true
wait "$PID"
XVFB_RC=$?
printf '%s\n' "$XVFB_RC" > "$RAW/xvfb-exit-code.txt"
exit 0