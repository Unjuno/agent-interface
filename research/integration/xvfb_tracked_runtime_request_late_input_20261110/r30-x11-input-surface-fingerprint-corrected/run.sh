#!/bin/sh
set +e
Xvfb :88 -screen 0 1280x720x24 -listen tcp -noreset -ac > /evidence/xvfb-88.log 2>&1 &
xvfb_88=$!
Xvfb :90 -screen 0 1280x720x24 -listen tcp -noreset -ac > /evidence/xvfb-90.log 2>&1 &
xvfb_90=$!
python3 -B /workspace/research/integration/xvfb_tracked_runtime_request_late_input_20261110/x11_delivery_proxy.py --listen-port 6089 --upstream-host 127.0.0.1 --upstream-port 6088 --control-path /tmp/ai-x11-r30.sock --ready-path /evidence/proxy-ready.json --events-path /evidence/proxy-events.jsonl > /evidence/proxy.log 2>&1 &
proxy=$!
ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20; do
  if [ -s /tmp/.X88-lock ] && [ -s /tmp/.X90-lock ] && [ -s /evidence/proxy-ready.json ] && python3 -c 'from Xlib import display; ds=[display.Display(x) for x in (":88", "127.0.0.1:88", "127.0.0.1:89", ":90")]; [d.close() for d in ds]' >/dev/null 2>&1; then ready=1; break; fi
  sleep 0.1
done
if [ "$ready" -ne 1 ]; then
  printf '{"status":"setup_failed","xvfb_88_pid":%s,"xvfb_90_pid":%s,"proxy_pid":%s}\n' "$xvfb_88" "$xvfb_90" "$proxy" > /evidence/DOCKER_EXIT.json
  cat /evidence/xvfb-88.log /evidence/xvfb-90.log /evidence/proxy.log
  kill -TERM "$proxy" "$xvfb_88" "$xvfb_90" 2>/dev/null
  wait "$proxy" 2>/dev/null; wait "$xvfb_88" 2>/dev/null; wait "$xvfb_90" 2>/dev/null
  exit 1
fi
python3 -B /workspace/research/integration/xvfb_tracked_runtime_request_late_input_20261110/r30-x11-input-surface-fingerprint-corrected/probe.py > /evidence/result.json 2> /evidence/probe.stderr
probe_status=$?
kill -TERM "$proxy" "$xvfb_88" "$xvfb_90" 2>/dev/null
wait "$proxy" 2>/dev/null; proxy_status=$?
wait "$xvfb_88" 2>/dev/null; xvfb_88_status=$?
wait "$xvfb_90" 2>/dev/null; xvfb_90_status=$?
printf '{"probe_exit_code":%s,"proxy_exit_code":%s,"xvfb_88_exit_code":%s,"xvfb_90_exit_code":%s,"xvfb_88_pid":%s,"xvfb_90_pid":%s,"proxy_pid":%s}\n' "$probe_status" "$proxy_status" "$xvfb_88_status" "$xvfb_90_status" "$xvfb_88" "$xvfb_90" "$proxy" > /evidence/DOCKER_EXIT.json
cat /evidence/result.json /evidence/probe.stderr
exit "$probe_status"
