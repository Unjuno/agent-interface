#!/usr/bin/env bash
set -eu
if [ "${AI_INTERFACE_XVFB_PRIVATE_NS:-0}" != 1 ]; then
  exec unshare --user --map-root-user --mount --fork env AI_INTERFACE_XVFB_PRIVATE_NS=1 bash "$0"
fi
ROOT=/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2/work/goal-currentmain-recovery-20261022
RAW="$ROOT/research/integration/standard_caller_xvfb_current_main_20261022/paused-server-matched-pilot-01/raw"
DEPS=/home/user/.cache/agent-interface-codex-deps-20261022-r02
mount --make-rprivate /
mount -t tmpfs -o mode=1777,nosuid,nodev tmpfs /tmp/.X11-unix
stat -c '%a %U:%G %n' /tmp/.X11-unix > "$RAW/private-mount-run.txt"
run_one() {
  TRIAL="$1"
  PAUSE_MS="$2"
  OUT="$RAW/$TRIAL"
  if test -S /tmp/.X11-unix/X88; then echo "display occupied before $TRIAL" >&2; return 81; fi
  /usr/bin/Xvfb :88 -nolisten tcp -screen 0 1024x768x24 -ac > "$OUT/xvfb.log" 2>&1 < /dev/null &
  PID=$!
  printf '%s\n' "$PID" > "$OUT/xvfb.pid"
  ready=0
  for i in $(seq 1 50); do
    if test -S /tmp/.X11-unix/X88 && kill -0 "$PID" 2>/dev/null; then ready=1; break; fi
    sleep 0.1
  done
  if test "$ready" != 1; then echo "XVFB_NOT_READY $TRIAL" >&2; kill -CONT "$PID" 2>/dev/null || true; kill -INT "$PID" 2>/dev/null || true; wait "$PID" || true; echo 71 > "$OUT/xvfb-exit-code.txt"; echo NOT_INVOKED > "$OUT/test-exit-code.txt"; return 0; fi
  readlink "/proc/$PID/exe" > "$OUT/xvfb-executable.txt"
  printf 'trial=%s\npause_ms=%s\npid=%s\n' "$TRIAL" "$PAUSE_MS" "$PID" > "$OUT/command.txt"
  set +e
  DISPLAY=:88 PYTHONPATH="$DEPS" \
  AGENT_INTERFACE_MCP_XVFB_TEST=1 \
  AGENT_INTERFACE_MCP_XVFB_PRESTARTED_CANCEL_SUPERVISOR=1 \
  AGENT_INTERFACE_MCP_XVFB_TRACE_OWNER_PROCESS_METHODS=1 \
  AGENT_INTERFACE_MCP_XVFB_CANCEL_ACK_WITHHOLD_S=1.0 \
  AGENT_INTERFACE_MCP_XVFB_SERVER_PAUSE_MS="$PAUSE_MS" \
  AGENT_INTERFACE_XVFB_PID="$PID" \
  AGENT_INTERFACE_MCP_XVFB_BLOCKED_RELEASE_RESULT="$OUT/result.json" \
  timeout --signal=TERM --kill-after=5s 45s python3 -m unittest -v runtime.cli_v1.test_mcp_xvfb_blocked_release_integration.StandardCallerBlockedReleaseXvfbTests.test_standard_caller_cancels_blocked_sync_and_releases_on_xvfb \
    > "$OUT/stdout.txt" 2> "$OUT/stderr.txt"
  RC=$?
  set -e
  printf '%s\n' "$RC" > "$OUT/test-exit-code.txt"
  kill -CONT "$PID" 2>/dev/null || true
  kill -INT "$PID" 2>/dev/null || true
  set +e
  wait "$PID"
  XVFB_RC=$?
  set -e
  printf '%s\n' "$XVFB_RC" > "$OUT/xvfb-exit-code.txt"
  printf '0\n' > "$OUT/wrapper-exit-code.txt"
}
printf 'starting=C01 arm=control\\n'; run_one C01 0; printf 'completed=C01\\n'
printf 'starting=P01 arm=paused\\n'; run_one P01 1500; printf 'completed=P01\\n'
printf 'starting=P02 arm=paused\\n'; run_one P02 1500; printf 'completed=P02\\n'
printf 'starting=C02 arm=control\\n'; run_one C02 0; printf 'completed=C02\\n'
printf 'starting=C03 arm=control\\n'; run_one C03 0; printf 'completed=C03\\n'
printf 'starting=P03 arm=paused\\n'; run_one P03 1500; printf 'completed=P03\\n'
if pgrep -x Xvfb >/dev/null; then echo 'Xvfb remains after sequence' > "$RAW/post-series-process-check.txt"; else echo 'No Xvfb process matched after sequence' > "$RAW/post-series-process-check.txt"; fi