#!/bin/sh
set +e
Xvfb :88 -screen 0 1280x720x24 -listen tcp -noreset -ac > /evidence/xvfb.log 2>&1 &
xvfb_pid=$!
export DISPLAY=:88 AGENT_INTERFACE_XVFB_PID="$xvfb_pid"
ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if python3 -c 'from Xlib import display; d=display.Display("127.0.0.1:88"); d.close()' >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.1
done
if [ "$ready" -ne 1 ]; then
  printf '{"status":"xvfb_tcp_start_failed","xvfb_pid":%s}\n' "$xvfb_pid" > /evidence/DOCKER_EXIT.json
  cat /evidence/xvfb.log; exit 1
fi
python3 -B /workspace/research/integration/xvfb_tracked_runtime_request_late_input_20261110/x11_delivery_proxy.py --listen-port 6089 --upstream-host 127.0.0.1 --upstream-port 6088 --control-path /tmp/ai-x11-delivery-r25.sock --ready-path /evidence/proxy-ready.json --events-path /evidence/proxy-events.jsonl > /evidence/proxy.log 2>&1 &
proxy_pid=$!
ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10; do
  if [ -s /evidence/proxy-ready.json ] && python3 -c 'from Xlib import display; d=display.Display("127.0.0.1:89"); d.close()' >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.1
done
if [ "$ready" -ne 1 ]; then
  printf '{"status":"proxy_start_failed","xvfb_pid":%s,"proxy_pid":%s}\n' "$xvfb_pid" "$proxy_pid" > /evidence/DOCKER_EXIT.json
  cat /evidence/xvfb.log /evidence/proxy.log; kill -TERM "$proxy_pid" "$xvfb_pid" 2>/dev/null; wait "$proxy_pid" 2>/dev/null; wait "$xvfb_pid" 2>/dev/null; exit 1
fi
AGENT_INTERFACE_MCP_XVFB_TEST=1 AGENT_INTERFACE_MCP_XVFB_DELAY_MS=800 AGENT_INTERFACE_MCP_XVFB_TRACKED_DELAYED_SECOND_PRESS=1 AGENT_INTERFACE_MCP_XVFB_SOCKET_DELIVERY_DELAY=1 AGENT_INTERFACE_MCP_XVFB_PROXY_DISPLAY=127.0.0.1:89 AGENT_INTERFACE_MCP_XVFB_PROXY_CONTROL=/tmp/ai-x11-delivery-r25.sock AGENT_INTERFACE_MCP_XVFB_PROXY_EVENTS=/evidence/proxy-events.jsonl AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=1.0 AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=0 AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT=/evidence/result.json AGENT_INTERFACE_MCP_XVFB_OBLIGATION_PUBLISHER_TRACE=/evidence/obligations.jsonl python3 -m unittest -v runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb > /evidence/test.log 2>&1
test_status=$?
cat /evidence/test.log
kill -TERM "$proxy_pid" "$xvfb_pid" 2>/dev/null
wait "$proxy_pid" 2>/dev/null; proxy_status=$?
wait "$xvfb_pid" 2>/dev/null; xvfb_status=$?
printf '{"test_exit_code":%s,"proxy_exit_code":%s,"xvfb_exit_code":%s,"xvfb_pid":%s,"proxy_pid":%s}\n' "$test_status" "$proxy_status" "$xvfb_status" "$xvfb_pid" "$proxy_pid" > /evidence/DOCKER_EXIT.json
exit "$test_status"
