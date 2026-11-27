#!/bin/sh
set +e
Xvfb :88 -screen 0 1280x720x24 -nolisten tcp -noreset -ac > /evidence/xvfb.log 2>&1 &
xvfb_pid=$!
export DISPLAY=:88 AGENT_INTERFACE_XVFB_PID="$xvfb_pid"
ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if python3 -c 'from Xlib import display; d=display.Display(); d.close()' >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.1
done
if [ "$ready" -ne 1 ]; then
  printf '{"status":"xvfb_start_failed","pid":%s}\n' "$xvfb_pid" > /evidence/DOCKER_EXIT.json
  cat /evidence/xvfb.log
  kill -TERM "$xvfb_pid" 2>/dev/null; wait "$xvfb_pid" 2>/dev/null
  exit 1
fi
python3 -m unittest -v runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb > /evidence/test.log 2>&1
test_status=$?
cat /evidence/test.log
kill -TERM "$xvfb_pid" 2>/dev/null
wait "$xvfb_pid" 2>/dev/null
x_status=$?
printf '{"test_exit_code":%s,"xvfb_exit_code":%s,"xvfb_pid":%s,"timeout_s":45}\n' "$test_status" "$x_status" "$xvfb_pid" > /evidence/DOCKER_EXIT.json
exit "$test_status"
